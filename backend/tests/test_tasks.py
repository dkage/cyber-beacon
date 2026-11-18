from datetime import UTC, date, datetime, timedelta

import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from planner.models import Task, TimeEntry
from planner.services import carry_forward, create_task, start_timer, stop_timer

pytestmark = pytest.mark.django_db


def test_task_lifecycle_and_stale_write(client, user):
    response = client.post(
        "/api/v1/tasks/", {"title": "Ship", "do_date": "2026-11-18", "due_date": "2026-11-20"}
    )
    assert response.status_code == 201
    task = response.json()
    url = f"/api/v1/tasks/{task['id']}/"
    assert client.patch(url, {"title": "No precondition"}).status_code == 428
    assert client.patch(url, {"do_date": "2026-11-19"}, HTTP_IF_MATCH='"1"').status_code == 200
    assert client.patch(url, {"title": "Stale"}, HTTP_IF_MATCH='"1"').status_code == 412
    response = client.patch(url, {"completed": True}, HTTP_IF_MATCH='"2"')
    assert response.json()["completed_at"]
    assert response.json()["due_date"] == "2026-11-20"
    assert client.delete(url, HTTP_IF_MATCH='"3"').status_code == 204
    assert client.get(url).status_code == 404
    assert Task.objects.get(pk=task["id"]).activity.filter(kind="trashed").exists()
    missing = client.post(url + "restore/")
    assert missing.status_code == 428
    assert "detail" in missing.json()
    stale = client.post(url + "restore/", HTTP_IF_MATCH='"3"')
    assert stale.status_code == 412
    assert "detail" in stale.json()
    assert client.post(url + "restore/", HTTP_IF_MATCH='"4"').status_code == 200
    assert client.get(url).status_code == 200


def test_cross_user_and_anonymous_access(client, user, other_user):
    task = create_task(other_user, {"title": "Private"})
    url = f"/api/v1/tasks/{task.pk}/"
    assert client.get(url).status_code == 404
    assert client.patch(url, {"title": "Stolen"}, HTTP_IF_MATCH='"1"').status_code == 404
    assert client.delete(url, HTTP_IF_MATCH='"1"').status_code == 404
    assert client.get("/api/v1/tasks/").json()["count"] == 0
    assert (
        client.post("/api/v1/tasks/", {"title": "Leak", "parent": str(task.pk)}).status_code == 400
    )
    assert APIClient().get("/api/v1/tasks/").status_code == 403


def test_parent_cycle_is_rejected(client, user):
    parent = create_task(user, {"title": "Parent"})
    child = create_task(user, {"title": "Child", "parent": parent})
    response = client.patch(
        f"/api/v1/tasks/{parent.pk}/", {"parent": str(child.pk)}, HTTP_IF_MATCH='"1"'
    )
    assert response.status_code == 400
    parent.refresh_from_db()
    assert parent.parent is None


def test_parent_is_rechecked_inside_the_mutation_lock(user):
    from django.utils import timezone as django_timezone
    from rest_framework.exceptions import ValidationError

    parent = create_task(user, {"title": "Parent"})
    Task.objects.filter(pk=parent.pk).update(deleted_at=django_timezone.now())
    with pytest.raises(ValidationError):
        create_task(user, {"title": "Child", "parent": parent})


def test_reorder_rejects_stale_membership_and_versions(client, user):
    a = create_task(user, {"title": "A", "do_date": date(2026, 11, 18)})
    b = create_task(user, {"title": "B", "do_date": date(2026, 11, 18)})
    payload = {
        "date": "2026-11-18",
        "items": [{"id": str(b.pk), "version": 1}, {"id": str(a.pk), "version": 1}],
    }
    response = client.post("/api/v1/tasks/reorder/", payload, format="json")
    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["B", "A"]
    assert client.post("/api/v1/tasks/reorder/", payload, format="json").status_code == 412
    payload["items"] = payload["items"][:1]
    assert client.post("/api/v1/tasks/reorder/", payload, format="json").status_code == 409


def test_validation_rejects_bad_dates_estimates_and_priority(client):
    for field, value in [
        ("do_date", "2026-11-18T00:00:00Z"),
        ("priority", 6),
        ("estimated_minutes", -1),
    ]:
        assert client.post("/api/v1/tasks/", {"title": "Bad", field: value}).status_code == 400


def test_timer_idempotency_and_owner_isolation(client, user, other_user):
    task = create_task(user, {"title": "Timed"})
    other = create_task(user, {"title": "Other"})
    entry = start_timer(user, task.pk)
    assert start_timer(user, task.pk).pk == entry.pk
    assert client.post("/api/v1/timers/start/", {"task": str(other.pk)}).status_code == 409
    stranger = create_task(other_user, {"title": "Secret"})
    assert client.post("/api/v1/timers/start/", {"task": str(stranger.pk)}).status_code == 404
    first = stop_timer(user, entry.pk).ended_at
    assert stop_timer(user, entry.pk).ended_at == first
    start_timer(user, task.pk)
    assert (
        client.patch(
            f"/api/v1/tasks/{task.pk}/", {"completed": True}, HTTP_IF_MATCH='"1"'
        ).status_code
        == 200
    )
    assert not TimeEntry.objects.filter(user=user, ended_at=None).exists()


def test_database_prevents_parallel_timers(user):
    task = create_task(user, {"title": "Timed"})
    start_timer(user, task.pk)
    with pytest.raises(IntegrityError), transaction.atomic():
        TimeEntry.objects.create(user=user, task=task, started_at=datetime.now(UTC))


def test_carry_forward_catches_up_and_preserves_independent_dates(user):
    task = create_task(
        user, {"title": "Unfinished", "do_date": date(2026, 11, 16), "due_date": date(2026, 11, 17)}
    )
    backlog = create_task(user, {"title": "Backlog"})
    done = create_task(
        user, {"title": "Done", "do_date": date(2026, 11, 16), "completed_at": datetime.now(UTC)}
    )
    now = datetime(2026, 11, 18, 3, 0, tzinfo=UTC)
    assert carry_forward(user, now) == 1
    assert carry_forward(user, now + timedelta(minutes=1)) == 0
    task.refresh_from_db()
    assert task.do_date == date(2026, 11, 18)
    assert task.due_date == date(2026, 11, 17)
    assert task.activity.filter(kind="carried_forward").count() == 2
    backlog.refresh_from_db()
    done.refresh_from_db()
    assert backlog.do_date is None
    assert done.do_date == date(2026, 11, 16)
