import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT)
    title = models.CharField(max_length=500)
    notes = models.TextField(blank=True, max_length=20000)
    do_date = models.DateField(null=True, blank=True, db_index=True)
    due_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    priority = models.PositiveSmallIntegerField(null=True, blank=True)
    estimated_minutes = models.PositiveIntegerField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position", "created_at", "id"]
        indexes = [models.Index(fields=["user", "do_date", "deleted_at"])]
        constraints = [
            models.CheckConstraint(
                condition=Q(priority__isnull=True) | Q(priority__lte=5), name="task_priority_range"
            ),
            models.CheckConstraint(
                condition=Q(estimated_minutes__isnull=True) | Q(estimated_minutes__lte=10080),
                name="task_estimate_range",
            ),
        ]


class TaskActivity(models.Model):
    task = models.ForeignKey(Task, on_delete=models.PROTECT, related_name="activity")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    kind = models.CharField(max_length=40)
    occurred_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict)

    class Meta:
        ordering = ["occurred_at", "pk"]


class TimeEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    task = models.ForeignKey(Task, on_delete=models.PROTECT, related_name="time_entries")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(ended_at__isnull=True),
                name="one_running_timer_per_user",
            ),
            models.CheckConstraint(
                condition=Q(ended_at__isnull=True) | Q(ended_at__gte=models.F("started_at")),
                name="time_entry_positive",
            ),
        ]
