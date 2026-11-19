from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from .models import Task, TimeEntry


def day_bounds(user, day):
    zone = ZoneInfo(user.timezone)
    start = datetime.combine(day, time.min, zone).astimezone(UTC)
    end = datetime.combine(day + timedelta(days=1), time.min, zone).astimezone(UTC)
    return start, end


def time_totals(user, day, now=None):
    now = now or timezone.now()
    start, end = day_bounds(user, day)
    totals = {}
    day_seconds = 0
    entries = TimeEntry.objects.filter(user=user)
    for entry in entries:
        finish = entry.ended_at or now
        duration = max(0, int((finish - entry.started_at).total_seconds()))
        key = str(entry.task_id)
        totals[key] = totals.get(key, 0) + duration
        day_seconds += max(
            0, int((min(finish, end) - max(entry.started_at, start)).total_seconds())
        )
    return totals, day_seconds


def capacity(user, day, events):
    zone = ZoneInfo(user.timezone)
    weekdays = user.work_weekdays if user.work_weekdays else [0, 1, 2, 3, 4]
    work_start = datetime.combine(day, user.work_start, zone).astimezone(UTC)
    work_end = datetime.combine(day, user.work_end, zone).astimezone(UTC)
    working = (
        max(0, int((work_end - work_start).total_seconds())) if day.weekday() in weekdays else 0
    )
    intervals = sorted(
        (max(event.starts_at, work_start), min(event.ends_at, work_end))
        for event in events
        if event.blocking
        and event.starts_at
        and event.ends_at
        and event.starts_at < work_end
        and event.ends_at > work_start
    )
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    meetings = sum(int((end - start).total_seconds()) for start, end in merged) if working else 0
    tasks = Task.objects.filter(user=user, do_date=day, deleted_at=None, completed_at=None)
    estimates = list(tasks.values_list("estimated_minutes", flat=True))
    available = max(0, working - meetings) // 60
    estimated = sum(value or 0 for value in estimates)
    return {
        "work_minutes": working // 60,
        "meeting_minutes": meetings // 60,
        "available_minutes": available,
        "estimated_minutes": estimated,
        "remaining_minutes": available - estimated,
        "unestimated_tasks": sum(value is None for value in estimates),
    }
