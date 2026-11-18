from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections
from django.utils import timezone
from django_q.models import Schedule

from jobs.models import JobRun
from jobs.schedules import ensure_schedules
from jobs.tasks import daily_tick
from planner.models import Task
from planner.services import PreconditionFailed, change_task, create_task


@pytest.mark.django_db(transaction=True)
def test_two_clients_cannot_both_commit_the_same_version(user):
    task = create_task(user, {"title": "Original"})

    def edit(title):
        close_old_connections()
        try:
            actor = get_user_model().objects.get(pk=user.pk)
            try:
                change_task(actor, task.pk, {"title": title}, 1)
                return "success"
            except PreconditionFailed:
                return "stale"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(edit, ["First writer", "Second writer"]))
    assert sorted(results) == ["stale", "success"]
    task.refresh_from_db()
    assert task.version == 2
    assert task.activity.filter(kind="edited").count() == 1


@pytest.mark.django_db
def test_schedules_recover_and_daily_tick_is_repeatable(user):
    ensure_schedules()
    ensure_schedules()
    assert Schedule.objects.filter(name__startswith="beacon-").count() == 2
    Schedule.objects.filter(name="beacon-daily-tick").update(minutes=99)
    ensure_schedules()
    assert Schedule.objects.get(name="beacon-daily-tick").minutes == 1
    task = create_task(user, {"title": "Overdue", "do_date": date(2020, 1, 1)})
    # A short controlled gap is sufficient; no thousands of historical rows.
    yesterday = timezone.localdate() - timedelta(days=1)
    Task.objects.filter(pk=task.pk).update(do_date=yesterday)
    daily_tick()
    daily_tick()
    task.refresh_from_db()
    assert task.do_date >= yesterday
    assert task.activity.filter(kind="carried_forward").count() <= 1
    assert JobRun.objects.filter(user=user, outcome="success").count() == 2


@pytest.mark.django_db
def test_local_midnight_and_dst_do_not_use_utc_date(user):
    from planner.services import carry_forward

    user.timezone = "America/New_York"
    user.save(update_fields=["timezone"])
    task = create_task(user, {"title": "Before fall-back", "do_date": date(2026, 10, 31)})
    assert carry_forward(user, datetime(2026, 11, 1, 3, 59, tzinfo=UTC)) == 0
    assert carry_forward(user, datetime(2026, 11, 1, 4, 0, tzinfo=UTC)) == 1
    assert carry_forward(user, datetime(2026, 11, 1, 7, 0, tzinfo=UTC)) == 0
    task.refresh_from_db()
    assert task.do_date == date(2026, 11, 1)
