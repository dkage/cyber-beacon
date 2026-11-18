import uuid
from datetime import UTC, date, datetime, time
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


def test_oauth_state_is_session_bound_expiring_and_one_use(user, notion, monkeypatch):
    from django.contrib.sessions.backends.db import SessionStore

    session = SessionStore()
    session.create()
    request = SimpleNamespace(user=user, session=session)
    url = services.begin_oauth(request, "notion")
    from urllib.parse import parse_qs, urlsplit

    state = parse_qs(urlsplit(url).query)["state"][0]
    monkeypatch.setattr(
        providers, "exchange", lambda *args: ({"access_token": "new"}, "workspace", "Work", [])
    )
    wrong = SessionStore()
    wrong.create()
    with pytest.raises(Exception, match="expired"):
        services.finish_oauth(SimpleNamespace(user=user, session=wrong), "notion", state, "code")
    services.finish_oauth(request, "notion", state, "code")
    with pytest.raises(Exception, match="expired"):
        services.finish_oauth(request, "notion", state, "code")
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
