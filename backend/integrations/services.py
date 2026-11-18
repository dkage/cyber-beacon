import hashlib
import json
import logging
import secrets
from datetime import timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework.exceptions import NotFound, ValidationError

from jobs.models import JobRun
from planner.services import Conflict, activity, create_task, lock_user

from . import providers
from .models import (
    CalendarEvent,
    ImportCommand,
    IntegrationConnection,
    Mount,
    MountSnapshot,
    OAuthState,
    TaskSource,
)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def owned_connection(user, pk):
    try:
        return IntegrationConnection.objects.get(user=user, pk=pk)
    except IntegrationConnection.DoesNotExist as exc:
        raise NotFound() from exc


def owned_mount(user, pk):
    try:
        return Mount.objects.select_related("connection").get(connection__user=user, pk=pk)
    except Mount.DoesNotExist as exc:
        raise NotFound() from exc


def begin_oauth(request, provider):
    providers.config(provider)
    if not request.session.session_key:
        request.session.save()
    OAuthState.objects.filter(expires_at__lt=timezone.now()).delete()
    token = secrets.token_urlsafe(32)
    OAuthState.objects.create(
        digest=digest(token),
        user=request.user,
        provider=provider,
        session_digest=digest(request.session.session_key),
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    return providers.authorize_url(provider, token)


def finish_oauth(request, provider, state, code):
    with transaction.atomic():
        row = (
            OAuthState.objects.select_for_update()
            .filter(
                digest=digest(state),
                provider=provider,
                user=request.user,
                session_digest=digest(request.session.session_key or ""),
                expires_at__gt=timezone.now(),
            )
            .first()
        )
        if not row:
            raise ValidationError(
                "This connection request expired or was already used. Start again."
            )
        row.delete()
    credentials, identity, label, scopes = providers.exchange(provider, code)
    with transaction.atomic():
        lock_user(request.user)
        connection, _ = IntegrationConnection.objects.get_or_create(
            user=request.user,
            provider=provider,
            account_identity=identity,
            defaults={"label": label},
        )
        previous = connection.credentials or {}
        connection.credentials = {**previous, **credentials}
        connection.scopes = scopes
        connection.status = "active"
        connection.last_error = ""
        connection.label = label[:255]
        connection.save()
        return connection


@transaction.atomic
def disconnect(user, connection):
    if connection.user_id != user.pk:
        raise NotFound()
    lock_user(user)
    connection.status = "disconnected"
    connection.credentials = None
    connection.save(update_fields=["status", "credentials"])
    connection.mounts.update(enabled=False)


def import_fingerprint(mount, external_id, day):
    return digest(json.dumps([str(mount.pk), external_id, str(day)], separators=(",", ":")))


def prior_import(user, key, fingerprint):
    command = ImportCommand.objects.filter(user=user, key=key).select_related("task").first()
    if command:
        if command.fingerprint != fingerprint:
            raise Conflict("This import key was already used for different input.")
        return command.task
    return None


def import_record(user, mount, external_id, day, key):
    if mount.connection.user_id != user.pk:
        raise NotFound()
    fingerprint = import_fingerprint(mount, external_id, day)
    previous = prior_import(user, key, fingerprint)
    if previous:
        return previous
    provider = mount.connection.provider
    if (
        provider not in {"notion", "github"}
        or mount.connection.status != "active"
        or not mount.enabled
    ):
        raise ValidationError("Choose an active worksheet source Mount.")
    if provider == "notion":
        raw = providers.page(mount.connection, external_id)
        if raw.get("parent", {}).get("data_source_id", "").replace(
            "-", ""
        ) != mount.external_id.replace("-", ""):
            raise ValidationError("This record does not belong to the selected data source.")
        title = providers.notion_title(raw)
        lines = []
        for name, value in raw.get("properties", {}).items():
            kind = value.get("type")
            if kind == "rich_text":
                text = "".join(part.get("plain_text", "") for part in value.get(kind, []))
            elif kind in {"select", "status"}:
                text = (value.get(kind) or {}).get("name", "")
            elif kind in {"number", "checkbox", "url", "email"}:
                text = str(value.get(kind) or "")
            else:
                continue
            if text:
                lines.append(f"{name}: {text}")
    else:
        if not external_id.isdigit():
            raise ValidationError("Choose a valid GitHub issue.")
        raw = providers.issue(mount, external_id)
        repository = raw.get("repository_url", "").rsplit("/repos/", 1)[-1]
        if (
            "pull_request" in raw
            or str(raw.get("number", "")) != external_id
            or repository.casefold() != mount.external_id.casefold()
        ):
            raise ValidationError("This issue does not belong to the selected repository.")
        title = f"#{external_id} {raw.get('title') or 'Untitled'}"[:500]
        lines = [f"GitHub issue #{external_id} · {raw.get('state', 'open')}"]
        if raw.get("body"):
            lines.append(raw["body"])
    with transaction.atomic():
        lock_user(user)
        previous = prior_import(user, key, fingerprint)
        if previous:
            return previous
        if not Mount.objects.filter(
            pk=mount.pk, enabled=True, connection__status="active"
        ).exists():
            raise Conflict("The Connection changed while importing. Refresh and try again.")
        task = create_task(
            user, {"title": title[:500], "notes": "\n".join(lines)[:20000], "do_date": day}
        )
        TaskSource.objects.create(
            task=task,
            mount=mount,
            external_id=external_id,
            raw=raw,
            url=(raw.get("url") or raw.get("html_url", ""))[:2000],
        )
        ImportCommand.objects.create(user=user, key=key, fingerprint=fingerprint, task=task)
        activity(task, "imported", user, provider=provider, external_id=external_id)
        return task


def event_values(raw, timezone_name=None):
    if "isAllDay" in raw:
        start, end = raw.get("start", {}), raw.get("end", {})
        if raw.get("isAllDay"):
            start_value, end_value = start.get("dateTime", ""), end.get("dateTime", "")
            target_timezone = ZoneInfo(timezone_name or "UTC")

            def local_date(value):
                parsed = parse_datetime(value)
                if parsed is None:
                    return None
                if timezone.is_naive(parsed):
                    parsed = timezone.make_aware(parsed, timezone=ZoneInfo("UTC"))
                return parsed.astimezone(target_timezone).date()

            return {
                "title": (raw.get("subject") or "Untitled meeting")[:500],
                "starts_at": None,
                "ends_at": None,
                "start_date": local_date(start_value),
                "end_date": local_date(end_value),
                "blocking": raw.get("showAs") != "free" and not raw.get("isCancelled"),
                "url": raw.get("webLink", "")[:2000],
            }
        return {
            "title": (raw.get("subject") or "Untitled meeting")[:500],
            "starts_at": parse_datetime(start.get("dateTime")),
            "ends_at": parse_datetime(end.get("dateTime")),
            "start_date": None,
            "end_date": None,
            "blocking": raw.get("showAs") != "free" and not raw.get("isCancelled"),
            "url": raw.get("webLink", "")[:2000],
        }
    start, end = raw.get("start", {}), raw.get("end", {})
    declined = any(
        person.get("self") and person.get("responseStatus") == "declined"
        for person in raw.get("attendees", [])
    )
    return {
        "title": raw.get("summary", "Untitled meeting")[:500],
        "starts_at": parse_datetime(start["dateTime"]) if "dateTime" in start else None,
        "ends_at": parse_datetime(end["dateTime"]) if "dateTime" in end else None,
        "start_date": parse_date(start["date"]) if "date" in start else None,
        "end_date": parse_date(end["date"]) if "date" in end else None,
        "blocking": raw.get("transparency") != "transparent" and not declined,
        "url": raw.get("htmlLink", "")[:2000],
    }


def sync_calendar(mount_id):
    """Lease, fetch without database locks, then replace a complete bounded window."""
    now = timezone.now()
    with transaction.atomic():
        mount = Mount.objects.select_for_update().select_related("connection").get(pk=mount_id)
        if not mount.enabled or mount.connection.status != "active":
            return
        if mount.sync_started_at and mount.sync_started_at > now - timedelta(minutes=3):
            return
        mount.sync_started_at = now
        mount.save(update_fields=["sync_started_at"])
    run = JobRun.objects.create(user=mount.connection.user, kind="calendar_sync")
    start, end = now - timedelta(days=30), now + timedelta(days=90)
    try:
        rows, cursor = [], None
        for _ in range(50):
            if mount.connection.provider == "microsoft":
                params = {
                    "startDateTime": start.isoformat(),
                    "endDateTime": end.isoformat(),
                    "$top": 250,
                    "$select": "id,subject,start,end,isAllDay,showAs,isCancelled,webLink,attendees",
                }
                path = cursor or f"me/calendars/{quote(mount.external_id, safe='')}/calendarView"
            else:
                params = {
                    "timeMin": start.isoformat(),
                    "timeMax": end.isoformat(),
                    "singleEvents": "true",
                    "maxResults": 250,
                    "showDeleted": "false",
                }
                if cursor:
                    params["pageToken"] = cursor
                path = f"calendars/{quote(mount.external_id, safe='')}/events"
            result = providers.request(
                mount.connection,
                "GET",
                path,
                params={} if mount.connection.provider == "microsoft" and cursor else params,
            )
            if mount.connection.provider == "microsoft":
                rows.extend(row for row in result.get("value", []) if not row.get("isCancelled"))
                cursor = result.get("@odata.nextLink")
            else:
                rows.extend(
                    row for row in result.get("items", []) if row.get("status") != "cancelled"
                )
                cursor = result.get("nextPageToken")
            if not cursor:
                break
        else:
            raise providers.ProviderError(
                "Calendar is too large for one refresh. Narrow the resource or retry later.",
                kind="fatal",
            )
        with transaction.atomic():
            locked = Mount.objects.select_for_update().get(pk=mount.pk)
            if (
                not locked.enabled
                or not IntegrationConnection.objects.filter(
                    pk=mount.connection_id, status="active"
                ).exists()
            ):
                raise providers.ProviderError(
                    "Connection was disabled during refresh.", kind="fatal"
                )
            # No partial replacement on provider or database failure.
            CalendarEvent.objects.filter(mount=mount).delete()
            CalendarEvent.objects.bulk_create(
                [
                    CalendarEvent(
                        mount=mount,
                        external_id=row["id"],
                        **event_values(row, mount.connection.user.timezone),
                    )
                    for row in rows
                ]
            )
            MountSnapshot.objects.update_or_create(
                mount=mount, defaults={"value": {"count": len(rows)}, "fetched_at": now}
            )
            locked.last_succeeded_at = now
            locked.last_error = ""
            locked.consecutive_failures = 0
            locked.sync_started_at = None
            locked.next_attempt_at = now + timedelta(minutes=5)
            locked.save()
        run.outcome = "success"
        run.counts = {"events": len(rows)}
    except Exception as exc:
        logging.getLogger(__name__).exception("Calendar refresh failed for Mount %s", mount.pk)
        error = (
            exc
            if isinstance(exc, providers.ProviderError)
            else providers.ProviderError("Calendar refresh failed. Previous data has been kept.")
        )
        with transaction.atomic():
            locked = Mount.objects.select_for_update().get(pk=mount.pk)
            locked.consecutive_failures += 1
            locked.last_error = str(error.detail)
            locked.sync_started_at = None
            locked.next_attempt_at = now + timedelta(
                seconds=max(
                    error.retry_after, min(3600, 60 * 2 ** min(locked.consecutive_failures, 6))
                )
            )
            if locked.consecutive_failures >= 5:
                locked.enabled = False
            locked.save()
        run.outcome, run.message = error.kind, str(error.detail)
    run.ended_at = timezone.now()
    run.save()


def events_for_day(user, day):
    from planner.day import day_bounds

    start, end = day_bounds(user, day)
    return (
        CalendarEvent.objects.filter(
            mount__connection__user=user,
            mount__enabled=True,
            mount__connection__status__in=["active", "needs_reauth"],
        )
        .filter(Q(starts_at__lt=end, ends_at__gt=start) | Q(start_date__lte=day, end_date__gt=day))
        .order_by("start_date", "starts_at", "pk")
    )
