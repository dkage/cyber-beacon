from datetime import timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, ValidationError

from .models import Task, TaskActivity, TimeEntry


class Conflict(APIException):
    status_code = 409
    default_detail = "State changed. Refresh and try again."


class PreconditionFailed(APIException):
    status_code = 412
    default_detail = "This Task changed elsewhere. Refresh before retrying your edit."


class PreconditionRequired(APIException):
    status_code = 428
    default_detail = 'Send If-Match: "<version>".'


def lock_user(user):
    return get_user_model().objects.select_for_update().get(pk=user.pk)


def require_version(task, version):
    if version is None:
        raise PreconditionRequired()
    if task.version != version:
        raise PreconditionFailed()


def owned_task(user, task_id, *, deleted=False):
    try:
        return Task.objects.get(pk=task_id, user=user, deleted_at__isnull=not deleted)
    except Task.DoesNotExist as exc:
        raise NotFound() from exc


def activity(task, kind, actor=None, **payload):
    TaskActivity.objects.create(task=task, actor=actor, kind=kind, payload=payload)


def next_position(user, day):
    return (
        Task.objects.filter(user=user, do_date=day, deleted_at=None).aggregate(p=Max("position"))[
            "p"
        ]
        or 0
    ) + 1


def validate_parent(user, task, parent):
    seen = {task.pk} if task else set()
    while parent:
        if parent.user_id != user.pk or parent.deleted_at:
            raise ValidationError({"parent": "Choose one of your active Tasks."})
        if parent.pk in seen:
            raise ValidationError({"parent": "Subtasks cannot form a cycle."})
        seen.add(parent.pk)
        parent = parent.parent


@transaction.atomic
def create_task(user, data):
    lock_user(user)
    validate_parent(user, None, data.get("parent"))
    task = Task.objects.create(user=user, position=next_position(user, data.get("do_date")), **data)
    activity(task, "created", user)
    return task


def stop_running(user, task=None, now=None):
    now = now or timezone.now()
    query = TimeEntry.objects.filter(user=user, ended_at=None)
    if task:
        query = query.filter(task=task)
    for entry in query:
        entry.ended_at = max(now, entry.started_at)
        entry.save(update_fields=["ended_at"])
        activity(entry.task, "timer_stopped", user, entry_id=str(entry.pk))


@transaction.atomic
def change_task(user, task_id, data, version, *, action="edit"):
    lock_user(user)
    task = owned_task(user, task_id, deleted=action == "restore")
    require_version(task, version)
    if "parent" in data:
        validate_parent(user, task, data["parent"])
    old_day = task.do_date
    if action == "delete":
        task.deleted_at = timezone.now()
        stop_running(user, task)
        activity(task, "trashed", user)
    elif action == "restore":
        task.deleted_at = None
        task.position = next_position(user, task.do_date)
        activity(task, "restored", user)
    else:
        completed = data.pop("completed", None)
        for key, value in data.items():
            setattr(task, key, value)
        if completed is not None and completed != bool(task.completed_at):
            task.completed_at = timezone.now() if completed else None
            if completed:
                stop_running(user, task)
            activity(task, "completed" if completed else "reopened", user)
        if old_day != task.do_date:
            task.position = next_position(user, task.do_date)
            activity(
                task,
                "rescheduled",
                user,
                from_date=str(old_day) if old_day else None,
                to_date=str(task.do_date) if task.do_date else None,
            )
        elif data:
            activity(task, "edited", user, fields=sorted(data))
    task.version += 1
    task.save()
    return task


@transaction.atomic
def reorder(user, day, items):
    lock_user(user)
    tasks = list(Task.objects.filter(user=user, do_date=day, deleted_at=None))
    submitted = {str(item["id"]): item["version"] for item in items}
    if len(submitted) != len(items) or set(submitted) != {str(task.pk) for task in tasks}:
        raise Conflict("The day's Tasks changed. Refresh before reordering.")
    by_id = {str(task.pk): task for task in tasks}
    for task in tasks:
        require_version(task, submitted[str(task.pk)])
    for index, item in enumerate(items):
        task = by_id[str(item["id"])]
        task.position = index
        task.version += 1
        task.save(update_fields=["position", "version", "updated_at"])
    return list(Task.objects.filter(user=user, do_date=day, deleted_at=None))


@transaction.atomic
def start_timer(user, task_id):
    lock_user(user)
    task = owned_task(user, task_id)
    if task.completed_at:
        raise Conflict("Reopen the Task before starting a timer.")
    current = TimeEntry.objects.filter(user=user, ended_at=None).first()
    if current:
        if current.task_id == task.pk:
            return current
        raise Conflict("Stop the current timer before starting another.")
    entry = TimeEntry.objects.create(user=user, task=task, started_at=timezone.now())
    activity(task, "timer_started", user, entry_id=str(entry.pk))
    return entry


@transaction.atomic
def stop_timer(user, entry_id):
    lock_user(user)
    try:
        entry = TimeEntry.objects.get(pk=entry_id, user=user)
    except TimeEntry.DoesNotExist as exc:
        raise NotFound() from exc
    if entry.ended_at is None:
        stop_running(user, entry.task)
        entry.refresh_from_db()
    return entry


@transaction.atomic
def carry_forward(user, now=None):
    user = lock_user(user)
    today = (now or timezone.now()).astimezone(ZoneInfo(user.timezone)).date()
    tasks = Task.objects.filter(user=user, deleted_at=None, completed_at=None, do_date__lt=today)
    count = 0
    for task in tasks:
        previous = task.do_date
        while previous < today:
            following = previous + timedelta(days=1)
            activity(
                task,
                "carried_forward",
                from_date=previous.isoformat(),
                to_date=following.isoformat(),
            )
            previous = following
        task.do_date = today
        task.position = next_position(user, today)
        task.version += 1
        task.save(update_fields=["do_date", "position", "version", "updated_at"])
        count += 1
    return count
