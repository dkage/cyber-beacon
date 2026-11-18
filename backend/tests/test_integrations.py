import uuid
from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace

import pytest
from cryptography.fernet import Fernet
from django.db import connection
from django.utils import timezone

from integrations import providers, services
from integrations.models import CalendarEvent, IntegrationConnection, Mount, OAuthState, TaskSource
from planner.day import capacity, time_totals
from planner.models import Task, TimeEntry
from planner.services import create_task

pytestmark = pytest.mark.django_db


@pytest.fixture
def notion(user, settings):
    settings.FERNET_KEYS = [Fernet.generate_key().decode()]
    settings.INTEGRATION_OAUTH = {
        "notion": {
            "client_id": "id",
            "client_secret": "secret",
            "redirect_uri": "http://localhost/callback",
        }
    }
    conn = IntegrationConnection.objects.create(
        user=user,
        provider="notion",
        account_identity="workspace",
        label="Work",
        credentials={"access_token": "secret-token"},
    )
    return Mount.objects.create(
        connection=conn, external_id="11111111-1111-1111-1111-111111111111", label="Tasks"
    )


def test_encryption_and_key_rotation(notion, settings):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT credentials FROM integrations_integrationconnection WHERE id = %s",
            [notion.connection_id],
        )
        encrypted = cursor.fetchone()[0]
    assert "secret-token" not in encrypted
    settings.FERNET_KEYS = [Fernet.generate_key().decode(), *settings.FERNET_KEYS]
    notion.connection.refresh_from_db()
    assert notion.connection.credentials["access_token"] == "secret-token"


def test_import_idempotency_repeat_and_local_fields(client, user, notion, monkeypatch):
    page_id = "22222222-2222-2222-2222-222222222222"
    raw = {
        "id": page_id,
        "parent": {"data_source_id": notion.external_id},
        "properties": {"Name": {"type": "title", "title": [{"plain_text": "Remote title"}]}},
        "url": "https://notion.so/test",
    }
    monkeypatch.setattr(providers, "page", lambda *args: raw)
    key = uuid.uuid4()
    task = services.import_record(user, notion, page_id, date(2026, 11, 18), key)
    assert services.import_record(user, notion, page_id, date(2026, 11, 18), key).pk == task.pk
    with pytest.raises(services.Conflict):
        services.import_record(user, notion, page_id, None, key)
    repeated = services.import_record(user, notion, page_id, None, uuid.uuid4())
    assert repeated.pk != task.pk
    response = client.patch(
        f"/api/v1/tasks/{task.pk}/",
        {"title": "My worksheet", "completed": True},
        HTTP_IF_MATCH='"1"',
    )
    assert response.status_code == 200
    assert TaskSource.objects.get(task=task).raw == raw
    services.disconnect(user, notion.connection)
    task.refresh_from_db()
    assert task.deleted_at is None
    assert task.title == "My worksheet"
    assert client.get("/api/v1/settings/").status_code == 200


def test_browse_does_not_create_tasks_and_cross_user_mount_rejected(
    client, other_user, notion, monkeypatch
):
    monkeypatch.setattr(
        providers,
        "browse",
        lambda *args: {"results": [{"id": "record", "properties": {}}], "next_cursor": "next"},
    )
    response = client.get(f"/api/v1/integrations/mounts/{notion.pk}/browse/")
    assert response.status_code == 200
    assert response.json()["next_cursor"] == "next"
    assert Task.objects.count() == 0
    notion.connection.user = other_user
    notion.connection.save(update_fields=["user"])
    assert client.get(f"/api/v1/integrations/mounts/{notion.pk}/browse/").status_code == 404


def test_github_import_count_is_scoped_to_the_selected_repository(
    client, user, notion, monkeypatch
):
    connection = notion.connection
    connection.provider = "github"
    connection.save(update_fields=["provider"])
    other_repository = Mount.objects.create(
        connection=connection, external_id="acme/other", label="acme/other"
    )
    notion.external_id = "acme/planner"
    notion.save(update_fields=["external_id"])
    task = create_task(user, {"title": "Imported issue"})
    TaskSource.objects.create(
        task=task,
        mount=notion,
        external_id="12",
        raw={"number": 12},
        url="https://github.com/acme/planner/issues/12",
    )
    monkeypatch.setattr(
        providers,
        "browse",
        lambda *args: {
            "results": [{"number": 12, "title": "Same number, different repository"}],
            "next_cursor": None,
        },
    )

    response = client.get(f"/api/v1/integrations/mounts/{other_repository.pk}/browse/")

    assert response.status_code == 200
    assert response.json()["results"][0]["id"] == "12"
    assert response.json()["results"][0]["imported_count"] == 0


def test_oauth_state_is_session_bound_expiring_and_one_use(user, notion, monkeypatch):
    from django.contrib.sessions.backends.db import SessionStore

    session = SessionStore()
    session.create()
    request = SimpleNamespace(user=user, session=session)
    url = services.begin_oauth(user, request.session.session_key, "notion")
    from urllib.parse import parse_qs, urlsplit

    state = parse_qs(urlsplit(url).query)["state"][0]
    monkeypatch.setattr(
        providers, "exchange", lambda *args: ({"access_token": "new"}, "workspace", "Work", [])
    )
    wrong = SessionStore()
    wrong.create()
    with pytest.raises(Exception, match="expired"):
        services.finish_oauth(user, wrong.session_key, "notion", state, "code")
    services.finish_oauth(user, request.session.session_key, "notion", state, "code")
    with pytest.raises(Exception, match="expired"):
        services.finish_oauth(user, request.session.session_key, "notion", state, "code")
    assert OAuthState.objects.count() == 0


def test_calendar_refresh_paginates_and_preserves_last_good_data(user, notion, monkeypatch):
    conn = notion.connection
    conn.provider = "google"
    conn.save(update_fields=["provider"])
    calls = []

    def fetch(conn, method, path, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return {
                "items": [
                    {
                        "id": "one",
                        "summary": "Review",
                        "start": {"dateTime": "2026-11-18T12:00:00Z"},
                        "end": {"dateTime": "2026-11-18T13:00:00Z"},
                    }
                ],
                "nextPageToken": "next",
            }
        return {
            "items": [
                {"id": "all-day", "start": {"date": "2026-11-18"}, "end": {"date": "2026-11-19"}}
            ]
        }

    monkeypatch.setattr(providers, "request", fetch)
    services.sync_calendar(notion.pk)
    assert len(calls) == 2
    assert calls[1]["params"]["pageToken"] == "next"
    assert CalendarEvent.objects.count() == 2
    assert Task.objects.count() == 0

    def fail(*args, **kwargs):
        raise providers.ProviderError("Rate limited", kind="rate_limited", retry_after=120)

    monkeypatch.setattr(providers, "request", fail)
    services.sync_calendar(notion.pk)
    notion.refresh_from_db()
    assert notion.last_error == "Rate limited"
    assert notion.last_succeeded_at
    assert notion.sync_started_at is None
    assert CalendarEvent.objects.count() == 2


def test_capacity_merges_overlapping_meetings_and_clips_work_hours(user):
    user.work_start, user.work_end = time(9), time(17)
    day = date(2026, 11, 18)

    def event(start, end, blocking=True):
        return SimpleNamespace(
            starts_at=datetime(2026, 11, 18, start, tzinfo=UTC),
            ends_at=datetime(2026, 11, 18, end, tzinfo=UTC),
            blocking=blocking,
        )

    create_task(user, {"title": "Plan", "do_date": day, "estimated_minutes": 120})
    create_task(user, {"title": "Unknown", "do_date": day})
    result = capacity(user, day, [event(11, 13), event(12, 14), event(15, 16, False)])
    assert result == {
        "work_minutes": 480,
        "meeting_minutes": 120,
        "available_minutes": 360,
        "estimated_minutes": 120,
        "remaining_minutes": 240,
        "unestimated_tasks": 1,
    }


def test_actuals_split_midnight_and_dst_days(user):
    user.timezone = "America/New_York"
    task = create_task(user, {"title": "Overnight"})
    TimeEntry.objects.create(
        user=user,
        task=task,
        started_at=datetime(2026, 11, 1, 3, 30, tzinfo=UTC),
        ended_at=datetime(2026, 11, 1, 7, 30, tzinfo=UTC),
    )
    totals, seconds = time_totals(user, date(2026, 11, 1))
    assert totals[str(task.pk)] == 4 * 3600
    assert seconds == 3.5 * 3600
    assert time_totals(user, date(2026, 10, 31))[1] == 1800


def test_notion_budget_and_sanitized_provider_errors(notion, monkeypatch):
    for _ in range(3):
        providers.take_budget(notion.connection)
    with pytest.raises(providers.ProviderError, match="budget"):
        providers.take_budget(notion.connection)
    import httpx

    monkeypatch.setattr(
        httpx,
        "request",
        lambda *args, **kwargs: httpx.Response(500, json={"secret": "never expose this"}),
    )
    with pytest.raises(providers.ProviderError) as error:
        providers.http("GET", "https://provider.test")
    assert "never expose" not in str(error.value.detail)


def test_day_read_model_serializes_tasks_sources_meetings_and_running_timer(client, user, notion):
    task = create_task(user, {"title": "Worksheet", "do_date": date(2026, 11, 18)})
    TaskSource.objects.create(
        task=task, mount=notion, external_id="record", raw={"title": "Remote"}
    )
    conn = notion.connection
    conn.provider = "google"
    conn.save(update_fields=["provider"])
    CalendarEvent.objects.create(
        mount=notion,
        external_id="event",
        title="Review",
        starts_at=datetime(2026, 11, 18, 12, tzinfo=UTC),
        ends_at=datetime(2026, 11, 18, 13, tzinfo=UTC),
    )
    TimeEntry.objects.create(user=user, task=task, started_at=timezone.now())
    response = client.get("/api/v1/day/?date=2026-11-18")
    assert response.status_code == 200
    result = response.json()
    assert result["tasks"][0]["source"]["raw"]["title"] == "Remote"
    assert result["events"][0]["mount"] == str(notion.pk)
    assert result["timer"]["task"] == str(task.pk)


def test_notion_oauth_protocol_stays_separate_from_login(notion, monkeypatch):
    import httpx

    def send(method, url, **kwargs):
        assert method == "POST"
        assert url == "https://api.notion.com/v1/oauth/token"
        assert kwargs["auth"] == ("id", "secret")
        assert kwargs["json"]["grant_type"] == "authorization_code"
        return httpx.Response(
            200,
            json={"access_token": "fresh", "workspace_id": "workspace", "workspace_name": "Work"},
        )

    monkeypatch.setattr(httpx, "request", send)
    credentials, identity, label, scopes = providers.exchange("notion", "code")
    assert credentials["access_token"] == "fresh"
    assert (identity, label, scopes) == ("workspace", "Work", [])


def test_google_exchange_refresh_and_readonly_scope(notion, settings, monkeypatch):
    import httpx

    settings.INTEGRATION_OAUTH["google"] = {
        "client_id": "google-id",
        "client_secret": "google-secret",
        "redirect_uri": "http://localhost/google/callback",
    }
    calls = []

    def send(method, url, **kwargs):
        calls.append((method, url))
        if url == "https://oauth2.googleapis.com/token":
            if kwargs["data"]["grant_type"] == "refresh_token":
                return httpx.Response(200, json={"access_token": "refreshed", "expires_in": 3600})
            return httpx.Response(
                200,
                json={
                    "access_token": "initial",
                    "refresh_token": "refresh",
                    "scope": providers.GOOGLE_SCOPE,
                    "expires_in": 3600,
                },
            )
        if url.endswith("calendars/primary"):
            return httpx.Response(200, json={"id": "account@example.test", "summary": "Work"})
        assert kwargs["headers"]["Authorization"] == "Bearer refreshed"
        return httpx.Response(200, json={"items": []})

    monkeypatch.setattr(httpx, "request", send)
    credentials, identity, label, scopes = providers.exchange("google", "code")
    assert scopes == [providers.GOOGLE_SCOPE]
    assert identity == "account@example.test"
    assert label == "account@example.test"
    credentials["expires_at"] = "2000-01-01T00:00:00+00:00"
    conn = notion.connection
    conn.provider, conn.credentials = "google", credentials
    conn.save(update_fields=["provider", "credentials"])
    providers.request(conn, "GET", "users/me/calendarList")
    conn.refresh_from_db()
    assert conn.credentials["refresh_token"] == "refresh"
    assert conn.credentials["access_token"] == "refreshed"
    assert len(calls) == 4


def test_google_oauth_selects_accounts_and_keeps_connections_independent(
    notion, settings, monkeypatch
):
    from urllib.parse import parse_qs, urlsplit

    from django.contrib.sessions.backends.db import SessionStore

    settings.INTEGRATION_OAUTH["google"] = {
        "client_id": "google-id",
        "client_secret": "google-secret",
        "redirect_uri": "http://localhost/google/callback",
    }
    request = SimpleNamespace(user=notion.connection.user, session=SessionStore())
    request.session.create()
    connections = []
    for email in ["personal@example.test", "work@example.test", "company@example.test"]:
        url = services.begin_oauth(request.user, request.session.session_key, "google")
        params = parse_qs(urlsplit(url).query)
        assert "select_account" in params["prompt"][0].split()
        state = params["state"][0]
        monkeypatch.setattr(
            providers,
            "exchange",
            lambda *args, email=email: (
                {"access_token": email},
                email,
                email,
                [providers.GOOGLE_SCOPE],
            ),
        )
        connections.append(
            services.finish_oauth(
                request.user, request.session.session_key, "google", state, "code"
            )
        )

    assert len({item.pk for item in connections}) == 3
    assert (
        IntegrationConnection.objects.filter(user=notion.connection.user, provider="google").count()
        == 3
    )
    assert [item.credentials["access_token"] for item in connections] == [
        "personal@example.test",
        "work@example.test",
        "company@example.test",
    ]


def test_dead_google_refresh_requires_reauthorization(notion, settings, monkeypatch):
    import httpx

    settings.INTEGRATION_OAUTH["google"] = {
        "client_id": "id",
        "client_secret": "secret",
        "redirect_uri": "http://localhost/callback",
    }
    conn = notion.connection
    conn.provider = "google"
    conn.credentials = {
        "access_token": "expired",
        "refresh_token": "dead",
        "expires_at": "2000-01-01T00:00:00+00:00",
    }
    conn.save(update_fields=["provider", "credentials"])
    monkeypatch.setattr(
        httpx,
        "request",
        lambda *args, **kwargs: httpx.Response(400, json={"error": "invalid_grant"}),
    )
    with pytest.raises(providers.ProviderError):
        providers.request(conn, "GET", "users/me/calendarList")
    conn.refresh_from_db()
    assert conn.status == "needs_reauth"


def test_microsoft_oauth_account_selection_and_refresh(notion, settings, monkeypatch):
    from urllib.parse import parse_qs, urlsplit

    import httpx

    settings.INTEGRATION_OAUTH["microsoft"] = {
        "client_id": "ms-id",
        "client_secret": "ms-secret",
        "redirect_uri": "http://localhost/microsoft/callback",
    }
    url = providers.authorize_url("microsoft", "state-token")
    query = parse_qs(urlsplit(url).query)
    assert query["prompt"] == ["select_account"]
    assert set(providers.MICROSOFT_SCOPES.split()).issubset(set(query["scope"][0].split()))
    calls = []

    def send(method, url, **kwargs):
        calls.append((method, url, kwargs))
        if url == providers.MICROSOFT_TOKEN:
            if kwargs["data"]["grant_type"] == "refresh_token":
                return httpx.Response(200, json={"access_token": "refreshed", "expires_in": 3600})
            return httpx.Response(
                200,
                json={"access_token": "initial", "refresh_token": "refresh", "expires_in": 3600},
            )
        return httpx.Response(
            200,
            json={"id": "oid-123", "mail": "person@example.test", "userPrincipalName": "person"},
        )

    monkeypatch.setattr(httpx, "request", send)
    credentials, identity, label, _ = providers.exchange("microsoft", "code")
    assert (identity, label) == ("oid-123", "person@example.test")
    credentials["expires_at"] = "2000-01-01T00:00:00+00:00"
    conn = notion.connection
    conn.provider, conn.credentials = "microsoft", credentials
    conn.save(update_fields=["provider", "credentials"])
    providers.request(conn, "GET", "me/calendars")
    assert calls[0][2]["data"]["scope"] == providers.MICROSOFT_SCOPES
    assert calls[-1][1] == "https://graph.microsoft.com/v1.0/me/calendars"
    conn.refresh_from_db()
    assert conn.credentials["access_token"] == "refreshed"


def test_microsoft_calendar_sync_paginates_and_maps_all_day_events(notion, settings, monkeypatch):
    import httpx

    settings.INTEGRATION_OAUTH["microsoft"] = {
        "client_id": "id",
        "client_secret": "secret",
        "redirect_uri": "http://localhost/callback",
    }
    conn = notion.connection
    conn.provider = "microsoft"
    conn.credentials = {"access_token": "token"}
    conn.save(update_fields=["provider", "credentials"])
    calls = []
    first_page = {
        "value": [
            {
                "id": "timed",
                "subject": "Planning",
                "start": {"dateTime": "2026-11-18T09:30:00Z", "timeZone": "UTC"},
                "end": {"dateTime": "2026-11-18T10:00:00Z", "timeZone": "UTC"},
                "isAllDay": False,
                "showAs": "busy",
                "webLink": "https://outlook.office.com/event/1",
            },
            {
                "id": "series-occurrence-1",
                "subject": "Weekly planning",
                "start": {"dateTime": "2026-11-18T14:00:00Z", "timeZone": "UTC"},
                "end": {"dateTime": "2026-11-18T14:30:00Z", "timeZone": "UTC"},
                "isAllDay": False,
                "showAs": "busy",
            },
        ],
        "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/calendars/cal/calendarView?$skip=1",
    }
    second_page = {
        "value": [
            {
                "id": "allday",
                "subject": "Holiday",
                "start": {"dateTime": "2026-11-19T03:00:00Z", "timeZone": "UTC"},
                "end": {"dateTime": "2026-11-20T03:00:00Z", "timeZone": "UTC"},
                "isAllDay": True,
                "showAs": "free",
                "isCancelled": False,
            },
            {
                "id": "series-occurrence-2",
                "subject": "Weekly planning",
                "start": {"dateTime": "2026-11-25T14:00:00Z", "timeZone": "UTC"},
                "end": {"dateTime": "2026-11-25T14:30:00Z", "timeZone": "UTC"},
                "isAllDay": False,
                "showAs": "busy",
            },
        ]
    }

    def send(method, url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(200, json=first_page if len(calls) == 1 else second_page)

    monkeypatch.setattr(httpx, "request", send)
    services.sync_calendar(str(notion.pk))
    events = list(CalendarEvent.objects.filter(mount=notion).order_by("external_id"))
    assert len(events) == 4
    assert {event.external_id for event in events if event.title == "Weekly planning"} == {
        "series-occurrence-1",
        "series-occurrence-2",
    }
    all_day = next(event for event in events if event.external_id == "allday")
    assert (all_day.start_date, all_day.end_date, all_day.blocking) == (
        date(2026, 11, 19),
        date(2026, 11, 20),
        False,
    )
    assert len(calls) == 2
    assert calls[0][1]["params"]["startDateTime"]
    assert calls[1][0] == first_page["@odata.nextLink"]


def test_microsoft_declined_meeting_does_not_block_capacity():
    values = services.event_values(
        {
            "subject": "Optional review",
            "start": {"dateTime": "2026-11-18T10:00:00Z"},
            "end": {"dateTime": "2026-11-18T11:00:00Z"},
            "showAs": "busy",
            "isAllDay": False,
            "responseStatus": {"response": "declined"},
        }
    )
    assert values["blocking"] is False


def test_calendar_dispatch_and_freshness_include_outlook(
    user, notion, monkeypatch, django_capture_on_commit_callbacks
):
    from jobs import tasks
    from planner.read_models import day_summary

    connection = notion.connection
    connection.provider = "microsoft"
    connection.save(update_fields=["provider"])
    queued = []
    monkeypatch.setattr("jobs.queue.enqueue", lambda *args: queued.append(args))

    with django_capture_on_commit_callbacks(execute=True):
        tasks.integration_tick()

    assert queued == [("integrations.services.sync_calendar", str(notion.pk))]
    freshness = day_summary(user, date(2026, 11, 18))["calendars"]
    assert [str(calendar["id"]) for calendar in freshness] == [str(notion.pk)]


def test_microsoft_calendar_failure_keeps_last_good_snapshot(notion, settings, monkeypatch):
    settings.INTEGRATION_OAUTH["microsoft"] = {
        "client_id": "id",
        "client_secret": "secret",
        "redirect_uri": "http://localhost/callback",
    }
    conn = notion.connection
    conn.provider = "microsoft"
    conn.credentials = {"access_token": "token"}
    conn.save(update_fields=["provider", "credentials"])
    prior = CalendarEvent.objects.create(
        mount=notion,
        external_id="kept",
        title="Last good event",
        starts_at=timezone.now(),
        ends_at=timezone.now() + timedelta(hours=1),
    )

    def fail(*args, **kwargs):
        raise providers.ProviderError("Calendar refresh failed.", kind="retryable")

    monkeypatch.setattr(providers, "request", fail)
    services.sync_calendar(str(notion.pk))
    assert CalendarEvent.objects.filter(pk=prior.pk, title="Last good event").exists()
    notion.refresh_from_db()
    assert notion.last_error == "Calendar refresh failed."
    assert notion.sync_started_at is None


def test_microsoft_provider_rejects_untrusted_next_link(notion, settings):
    settings.INTEGRATION_OAUTH["microsoft"] = {
        "client_id": "id",
        "client_secret": "secret",
        "redirect_uri": "http://localhost/callback",
    }
    conn = notion.connection
    conn.provider = "microsoft"
    conn.credentials = {"access_token": "token"}
    conn.save(update_fields=["provider", "credentials"])
    with pytest.raises(providers.ProviderError, match="invalid page URL"):
        providers.request(conn, "GET", "https://attacker.example/steal")


def test_github_app_oauth_and_repository_browser(notion, settings, monkeypatch):
    from urllib.parse import parse_qs, urlsplit

    settings.INTEGRATION_OAUTH["github"] = {
        "client_id": "app-id",
        "client_secret": "app-secret",
        "redirect_uri": "http://localhost/github/callback",
    }
    url = providers.authorize_url("github", "state-token")
    authorize_query = parse_qs(urlsplit(url).query)
    assert authorize_query["state"] == ["state-token"]
    assert "scope" not in authorize_query
    calls = []

    def request(connection, method, path, **kwargs):
        calls.append((method, path, kwargs))
        return [
            {"full_name": "acme/one"},
            {"full_name": "acme/two"},
        ]

    monkeypatch.setattr(providers, "request", request)
    conn = notion.connection
    conn.provider = "github"
    conn.credentials = {"access_token": "token"}
    conn.save(update_fields=["provider", "credentials"])
    result = providers.resources(conn, query="two")
    assert result == {"results": [{"id": "acme/two", "label": "acme/two"}], "next_cursor": None}
    assert calls[0][1] == "user/repos"
    assert calls[0][2]["params"]["affiliation"] == "owner,collaborator,organization_member"


def test_github_user_token_exchange_and_refresh(notion, settings, monkeypatch):
    import httpx

    settings.INTEGRATION_OAUTH["github"] = {
        "client_id": "app-id",
        "client_secret": "app-secret",
        "redirect_uri": "http://localhost/github/callback",
    }
    calls = []

    def send(method, url, **kwargs):
        calls.append((method, url, kwargs))
        if url == "https://github.com/login/oauth/access_token":
            if kwargs["data"].get("grant_type") == "refresh_token":
                return httpx.Response(
                    200,
                    json={
                        "access_token": "refreshed",
                        "refresh_token": "rotated-refresh",
                        "expires_in": 28800,
                    },
                )
            return httpx.Response(
                200,
                json={
                    "access_token": "initial",
                    "refresh_token": "refresh",
                    "expires_in": 28800,
                },
            )
        if url == "https://api.github.com/user":
            return httpx.Response(200, json={"id": 42, "login": "dev", "name": "Developer"})
        assert kwargs["headers"]["Authorization"] == "Bearer refreshed"
        return httpx.Response(200, json=[])

    monkeypatch.setattr(httpx, "request", send)
    credentials, identity, label, scopes = providers.exchange("github", "authorization-code")
    assert (identity, label, scopes) == ("42", "Developer", [])
    assert "grant_type" not in calls[0][2]["data"]
    credentials["expires_at"] = "2000-01-01T00:00:00+00:00"
    conn = notion.connection
    conn.provider, conn.credentials = "github", credentials
    conn.save(update_fields=["provider", "credentials"])
    assert providers.request(conn, "GET", "user/repos") == []
    conn.refresh_from_db()
    assert conn.credentials["access_token"] == "refreshed"
    assert conn.credentials["refresh_token"] == "rotated-refresh"


def test_github_http_accepts_repository_array_responses(monkeypatch):
    import httpx

    monkeypatch.setattr(
        httpx, "request", lambda *args, **kwargs: httpx.Response(200, json=[{"id": 1}])
    )
    assert providers.http("GET", "https://api.github.com/user/repos") == [{"id": 1}]


def test_github_issue_search_filters_pull_requests_and_builds_query(notion, monkeypatch):
    calls = []

    def request(connection, method, path, **kwargs):
        calls.append((method, path, kwargs))
        return {
            "total_count": 51,
            "items": [
                {"number": 12, "title": "Fix the bug"},
                {"number": 13, "title": "A pull request", "pull_request": {}},
            ],
        }

    monkeypatch.setattr(providers, "request", request)
    notion.connection.provider = "github"
    notion.external_id = "acme/planner"
    page = providers.browse(notion, "1", "regression crash")
    assert page["results"] == [{"number": 12, "title": "Fix the bug"}]
    assert page["next_cursor"] == "2"
    assert calls[0][1] == "search/issues"
    assert calls[0][2]["params"]["q"] == "repo:acme/planner is:issue regression crash"


def test_github_browse_uses_issue_number_as_import_identity(user, client, notion, monkeypatch):
    notion.connection.provider = "github"
    notion.connection.save(update_fields=["provider"])
    notion.external_id = "acme/planner"
    notion.save(update_fields=["external_id"])
    task = create_task(user, {"title": "Existing issue worksheet"})
    TaskSource.objects.create(
        task=task,
        mount=notion,
        external_id="12",
        raw={},
        url="https://github.com/acme/planner/issues/12",
    )
    monkeypatch.setattr(
        providers,
        "browse",
        lambda *args: {
            "results": [
                {
                    "id": 987654,
                    "number": 12,
                    "title": "Fix regression",
                    "html_url": "https://github.com/acme/planner/issues/12",
                }
            ],
            "next_cursor": None,
        },
    )
    client.force_login(user)
    response = client.get(f"/api/v1/integrations/mounts/{notion.pk}/browse/")
    assert response.status_code == 200
    assert response.json()["results"] == [
        {
            "id": "12",
            "title": "#12 Fix regression",
            "url": "https://github.com/acme/planner/issues/12",
            "imported_count": 1,
        }
    ]


def test_github_issue_import_creates_local_worksheet_and_checks_repository(
    user, notion, monkeypatch
):
    notion.connection.provider = "github"
    notion.connection.save(update_fields=["provider"])
    notion.external_id = "acme/planner"
    notion.save(update_fields=["external_id"])
    raw = {
        "number": 12,
        "title": "Repair the planner",
        "body": "Steps to reproduce",
        "state": "open",
        "repository_url": "https://api.github.com/repos/acme/planner",
        "html_url": "https://github.com/acme/planner/issues/12",
    }
    monkeypatch.setattr(providers, "issue", lambda mount, external_id: raw)
    task = services.import_record(user, notion, "12", date(2026, 11, 18), uuid.uuid4())
    task.refresh_from_db()
    source = TaskSource.objects.get(task=task)
    assert task.title == "#12 Repair the planner"
    assert "Steps to reproduce" in task.notes
    assert source.external_id == "12"
    assert source.url == raw["html_url"]
    assert source.raw == raw
    assert task.activity.order_by("-occurred_at").first().payload["provider"] == "github"

    raw["repository_url"] = "https://api.github.com/repos/acme/other"
    with pytest.raises(services.ValidationError, match="does not belong"):
        services.import_record(user, notion, "12", None, uuid.uuid4())


def test_notion_record_search_uses_title_property_id(notion, monkeypatch):
    calls = []

    def request(conn, method, path, **kwargs):
        calls.append((method, path, kwargs))
        if method == "GET":
            return {"properties": {"Renamed title": {"type": "title", "id": "title-id"}}}
        return {"results": [], "next_cursor": None}

    monkeypatch.setattr(providers, "request", request)
    providers.browse(notion, "cursor", "release")
    assert calls[-1][2]["json"]["filter"] == {
        "property": "title-id",
        "title": {"contains": "release"},
    }
    assert calls[-1][2]["json"]["start_cursor"] == "cursor"
    assert Task.objects.count() == 0


def test_import_and_disconnect_enforce_service_ownership(other_user, notion):
    from rest_framework.exceptions import NotFound

    with pytest.raises(NotFound):
        services.import_record(other_user, notion, "record", None, uuid.uuid4())
    with pytest.raises(NotFound):
        services.disconnect(other_user, notion.connection)
    notion.connection.refresh_from_db()
    assert notion.connection.status == "active"
    assert Task.objects.count() == 0
