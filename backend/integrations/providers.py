import re
from datetime import timedelta
from urllib.parse import quote, urlencode

import httpx
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import APIException

from .models import IntegrationConnection

NOTION_VERSION = "2025-09-03"
GOOGLE_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
MICROSOFT_SCOPES = "User.Read Calendars.Read offline_access"
MICROSOFT_AUTH = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN = "https://login.microsoftonline.com/common/oauth2/v2.0/token"


class ProviderError(APIException):
    status_code = 502
    default_detail = "Provider request failed. Try again later."

    def __init__(self, detail=None, *, kind="retryable", retry_after=60):
        self.kind = kind
        self.retry_after = retry_after
        super().__init__(detail)


def http(method, url, **kwargs):
    try:
        response = httpx.request(method, url, timeout=15, follow_redirects=False, **kwargs)
    except httpx.HTTPError as exc:
        raise ProviderError("Provider is unreachable. Try again later.") from exc
    if response.status_code == 429:
        try:
            delay = max(1, min(3600, int(response.headers.get("Retry-After", "60"))))
        except ValueError:
            delay = 60
        raise ProviderError(
            "Provider rate limit reached. Try again shortly.",
            kind="rate_limited",
            retry_after=delay,
        )
    if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
        try:
            delay = max(
                1,
                min(
                    3600,
                    int(response.headers.get("X-RateLimit-Reset", "0"))
                    - int(timezone.now().timestamp()),
                ),
            )
        except ValueError:
            delay = 60
        raise ProviderError(
            "GitHub rate limit reached. Try again shortly.",
            kind="rate_limited",
            retry_after=delay,
        )
    if response.status_code in {401, 403}:
        raise ProviderError(
            "Reconnect this Provider or check its resource permissions.", kind="auth_dead"
        )
    if response.status_code >= 400:
        raise ProviderError(kind="retryable" if response.status_code >= 500 else "fatal")
    try:
        body = response.json()
        if not isinstance(body, (dict, list)):
            raise ValueError()
        return body
    except ValueError as exc:
        raise ProviderError("Provider returned an unreadable response.") from exc


def config(provider):
    cfg = settings.INTEGRATION_OAUTH.get(provider, {})
    if (
        not all(cfg.get(field) for field in ["client_id", "client_secret", "redirect_uri"])
        or not settings.FERNET_KEYS
    ):
        error = ProviderError(
            "Configure this Provider's OAuth client and encryption key on the server.", kind="fatal"
        )
        error.status_code = 503
        raise error
    return cfg


def authorize_url(provider, state):
    cfg = config(provider)
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "response_type": "code",
        "state": state,
    }
    if provider == "notion":
        params["owner"] = "user"
        return "https://api.notion.com/v1/oauth/authorize?" + urlencode(params)
    if provider == "microsoft":
        params.update(scope=MICROSOFT_SCOPES, prompt="select_account")
        return MICROSOFT_AUTH + "?" + urlencode(params)
    if provider == "github":
        return "https://github.com/login/oauth/authorize?" + urlencode(params)
    params.update(scope=GOOGLE_SCOPE, access_type="offline", prompt="consent select_account")
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


def exchange(provider, code):
    cfg = config(provider)
    data = {"grant_type": "authorization_code", "code": code, "redirect_uri": cfg["redirect_uri"]}
    if provider == "notion":
        result = http(
            "POST",
            "https://api.notion.com/v1/oauth/token",
            json=data,
            auth=(cfg["client_id"], cfg["client_secret"]),
        )
        return (
            result,
            result["workspace_id"],
            result.get("workspace_name") or "Notion workspace",
            [],
        )
    if provider == "microsoft":
        data.update(
            client_id=cfg["client_id"], client_secret=cfg["client_secret"], scope=MICROSOFT_SCOPES
        )
        result = http("POST", MICROSOFT_TOKEN, data=data)
        result["expires_at"] = (
            timezone.now() + timedelta(seconds=result.get("expires_in", 3600))
        ).isoformat()
        account = http(
            "GET",
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": "Bearer " + result["access_token"]},
        )
        identity = account.get("id") or account.get("userPrincipalName")
        label = account.get("mail") or account.get("userPrincipalName") or identity
        if not identity:
            raise ProviderError("Microsoft did not return an account identity.", kind="fatal")
        return result, identity, label, result.get("scope", "").split()
    if provider == "github":
        data.pop("grant_type")
        data.update(client_id=cfg["client_id"], client_secret=cfg["client_secret"])
        result = http(
            "POST",
            "https://github.com/login/oauth/access_token",
            data=data,
            headers={"Accept": "application/json"},
        )
        if result.get("expires_in"):
            result["expires_at"] = (
                timezone.now() + timedelta(seconds=result["expires_in"])
            ).isoformat()
        account = http(
            "GET",
            "https://api.github.com/user",
            headers={"Authorization": "Bearer " + result["access_token"]},
        )
        identity = str(account["id"])
        return result, identity, account.get("name") or account["login"], []
    data.update(client_id=cfg["client_id"], client_secret=cfg["client_secret"])
    result = http("POST", "https://oauth2.googleapis.com/token", data=data)
    if GOOGLE_SCOPE not in result.get("scope", "").split():
        raise ProviderError("Calendar read permission was not granted.", kind="fatal")
    result["expires_at"] = (
        timezone.now() + timedelta(seconds=result.get("expires_in", 3600))
    ).isoformat()
    # Stable Google Calendar account identity without adding login scopes.
    account = http(
        "GET",
        "https://www.googleapis.com/calendar/v3/calendars/primary",
        headers={"Authorization": "Bearer " + result["access_token"]},
    )
    return (
        result,
        account["id"],
        account.get("summary") or account["id"],
        result.get("scope", "").split(),
    )


@transaction.atomic
def take_budget(connection):
    locked = IntegrationConnection.objects.select_for_update().get(pk=connection.pk)
    now = timezone.now()
    tokens = min(3.0, locked.budget_tokens + (now - locked.budget_at).total_seconds() * 3)
    if tokens < 1:
        raise ProviderError(
            "Provider request budget is busy. Try again shortly.",
            kind="rate_limited",
            retry_after=1,
        )
    locked.budget_tokens = tokens - 1
    locked.budget_at = now
    locked.save(update_fields=["budget_tokens", "budget_at"])


def request(connection, method, path, **kwargs):
    if connection.status != "active" or not connection.credentials:
        raise ProviderError("Reconnect this Provider before continuing.", kind="auth_dead")
    credentials = connection.credentials
    if connection.provider in {"google", "microsoft", "github"}:
        expires = credentials.get("expires_at")
        if expires and timezone.now() >= parse_datetime(expires):
            cfg = config(connection.provider)
            if not credentials.get("refresh_token"):
                raise ProviderError("Reconnect this Provider account.", kind="auth_dead")
            try:
                refresh_data = {
                    "grant_type": "refresh_token",
                    "refresh_token": credentials["refresh_token"],
                    "client_id": cfg["client_id"],
                    "client_secret": cfg["client_secret"],
                }
                if connection.provider == "microsoft":
                    refresh_data["scope"] = MICROSOFT_SCOPES
                elif connection.provider == "github":
                    refresh_data.update(
                        grant_type="refresh_token",
                        refresh_token=credentials["refresh_token"],
                    )
                refreshed = http(
                    "POST",
                    MICROSOFT_TOKEN
                    if connection.provider == "microsoft"
                    else "https://github.com/login/oauth/access_token"
                    if connection.provider == "github"
                    else "https://oauth2.googleapis.com/token",
                    data=refresh_data,
                    **(
                        {"headers": {"Accept": "application/json"}}
                        if connection.provider == "github"
                        else {}
                    ),
                )
            except ProviderError as exc:
                if exc.kind == "fatal":
                    exc.kind = "auth_dead"
                if exc.kind == "auth_dead":
                    IntegrationConnection.objects.filter(pk=connection.pk).update(
                        status="needs_reauth", last_error="Reconnect this Provider account."
                    )
                raise
            credentials = {
                **credentials,
                **refreshed,
                "expires_at": (
                    timezone.now() + timedelta(seconds=refreshed.get("expires_in", 3600))
                ).isoformat(),
            }
            IntegrationConnection.objects.filter(pk=connection.pk, status="active").update(
                credentials=credentials
            )
            connection.credentials = credentials
        if connection.provider == "microsoft":
            base = "https://graph.microsoft.com/v1.0/"
            headers = {
                "Authorization": "Bearer " + credentials["access_token"],
                "Prefer": 'outlook.timezone="UTC", IdType="ImmutableId"',
            }
        elif connection.provider == "github":
            take_budget(connection)
            base = "https://api.github.com/"
            headers = {
                "Authorization": "Bearer " + credentials["access_token"],
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        else:
            base = "https://www.googleapis.com/calendar/v3/"
            headers = {"Authorization": "Bearer " + credentials["access_token"]}
    else:
        take_budget(connection)
        base = "https://api.notion.com/v1/"
        headers = {
            "Authorization": "Bearer " + credentials["access_token"],
            "Notion-Version": NOTION_VERSION,
        }
    try:
        if connection.provider in {"microsoft", "github"} and path.startswith("https://"):
            allowed_origin = (
                "https://graph.microsoft.com/v1.0/"
                if connection.provider == "microsoft"
                else "https://api.github.com/"
            )
            if not path.startswith(allowed_origin):
                raise ProviderError("Provider returned an invalid page URL.", kind="fatal")
            url = path
        else:
            url = base + path
        return http(method, url, headers=headers, **kwargs)
    except ProviderError as exc:
        if exc.kind == "auth_dead":
            IntegrationConnection.objects.filter(pk=connection.pk).update(
                status="needs_reauth", last_error=str(exc.detail)
            )
        raise


def notion_title(record):
    title = record.get("title", [])
    for value in record.get("properties", {}).values():
        if value.get("type") == "title":
            title = value.get("title", [])
            break
    return (
        "".join(part.get("plain_text", part.get("text", {}).get("content", "")) for part in title)[
            :500
        ]
        or "Untitled"
    )


def valid_repository_name(value):
    return bool(re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9_.-]+", value))


def resources(connection, cursor="", query=""):
    if connection.provider == "notion":
        body = {"filter": {"value": "data_source", "property": "object"}, "page_size": 50}
        if cursor:
            body["start_cursor"] = cursor
        if query:
            body["query"] = query
        result = request(connection, "POST", "search", json=body)
        return {
            "results": [
                {"id": row["id"], "label": notion_title(row)} for row in result.get("results", [])
            ],
            "next_cursor": result.get("next_cursor"),
        }
    if connection.provider == "microsoft":
        params = {"$top": 50, "$select": "id,name"}
        result = request(
            connection,
            "GET",
            cursor if cursor.startswith("https://") else "me/calendars",
            params={} if cursor else params,
        )
        return {
            "results": [
                {"id": row["id"], "label": row.get("name") or row["id"]}
                for row in result.get("value", [])
            ],
            "next_cursor": result.get("@odata.nextLink"),
        }
    if connection.provider == "github":
        page_number = min(100_000, int(cursor)) if cursor.isdigit() else 1
        rows = request(
            connection,
            "GET",
            "user/repos",
            params={
                "per_page": 50,
                "page": page_number,
                "sort": "updated",
                "affiliation": "owner,collaborator,organization_member",
            },
        )
        if not isinstance(rows, list):
            raise ProviderError("GitHub returned an unreadable repository list.")
        has_next = len(rows) == 50
        if query:
            normalized = query.casefold()
            rows = [row for row in rows if normalized in row.get("full_name", "").casefold()]
        return {
            "results": [{"id": row["full_name"], "label": row["full_name"]} for row in rows],
            "next_cursor": str(page_number + 1) if has_next else None,
        }
    params = {"maxResults": 50}
    if cursor:
        params["pageToken"] = cursor
    result = request(connection, "GET", "users/me/calendarList", params=params)
    return {
        "results": [
            {"id": row["id"], "label": row.get("summary", row["id"])}
            for row in result.get("items", [])
            if not row.get("deleted")
        ],
        "next_cursor": result.get("nextPageToken"),
    }


def browse(mount, cursor="", query=""):
    if mount.connection.provider == "github":
        if not valid_repository_name(mount.external_id):
            raise ProviderError("This GitHub repository Mount is invalid.", kind="fatal")
        page_number = min(20, int(cursor)) if cursor.isdigit() else 1
        terms = [f"repo:{mount.external_id}", "is:issue"]
        if query.strip():
            terms.append(query.strip())
        result = request(
            mount.connection,
            "GET",
            "search/issues",
            params={"q": " ".join(terms), "per_page": 50, "page": page_number},
        )
        rows = [row for row in result.get("items", []) if "pull_request" not in row]
        return {
            "results": rows,
            "next_cursor": str(page_number + 1)
            if page_number * 50 < min(result.get("total_count", 0), 1000)
            else None,
        }
    body = {"page_size": 50}
    if cursor:
        body["start_cursor"] = cursor
    if query:
        schema = request(
            mount.connection, "GET", f"data_sources/{quote(mount.external_id, safe='')}"
        )
        title = next(
            (
                value["id"]
                for value in schema.get("properties", {}).values()
                if value.get("type") == "title"
            ),
            None,
        )
        if title:
            body["filter"] = {"property": title, "title": {"contains": query}}
    return request(
        mount.connection,
        "POST",
        f"data_sources/{quote(mount.external_id, safe='')}/query",
        json=body,
    )


def page(connection, external_id):
    return request(connection, "GET", f"pages/{quote(external_id, safe='')}")


def issue(mount, external_id):
    if mount.connection.provider != "github" or not re.fullmatch(r"\d{1,10}", external_id):
        raise ProviderError("This GitHub issue reference is invalid.", kind="fatal")
    if not valid_repository_name(mount.external_id):
        raise ProviderError("This GitHub repository Mount is invalid.", kind="fatal")
    repository = quote(mount.external_id, safe="/")
    return request(mount.connection, "GET", f"repos/{repository}/issues/{external_id}")
