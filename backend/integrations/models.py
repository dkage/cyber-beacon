import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from .fields import EncryptedJSONField


class IntegrationConnection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    provider = models.CharField(
        max_length=20,
        choices=[
            ("notion", "Notion"),
            ("google", "Google Calendar"),
            ("microsoft", "Outlook Calendar"),
            ("github", "GitHub Issues"),
        ],
    )
    account_identity = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    credentials = EncryptedJSONField(null=True)
    scopes = models.JSONField(default=list)
    status = models.CharField(max_length=30, default="active")
    last_error = models.CharField(max_length=500, blank=True)
    budget_tokens = models.FloatField(default=3)
    budget_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "provider", "account_identity"], name="unique_provider_account"
            )
        ]


class Mount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connection = models.ForeignKey(
        IntegrationConnection, on_delete=models.PROTECT, related_name="mounts"
    )
    external_id = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    sync_started_at = models.DateTimeField(null=True)
    last_succeeded_at = models.DateTimeField(null=True)
    last_error = models.CharField(max_length=500, blank=True)
    consecutive_failures = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["connection", "external_id"], name="unique_mount_resource"
            )
        ]


class MountSnapshot(models.Model):
    mount = models.OneToOneField(Mount, primary_key=True, on_delete=models.PROTECT)
    value = models.JSONField(default=dict)
    fetched_at = models.DateTimeField(default=timezone.now)


class TaskSource(models.Model):
    task = models.OneToOneField("planner.Task", on_delete=models.PROTECT, related_name="source")
    mount = models.ForeignKey(Mount, on_delete=models.PROTECT)
    external_id = models.CharField(max_length=255)
    url = models.URLField(max_length=2000, blank=True)
    raw = models.JSONField(default=dict)
    imported_at = models.DateTimeField(default=timezone.now)


class ImportCommand(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    task = models.ForeignKey("planner.Task", on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "key"], name="unique_import_command")
        ]


class OAuthState(models.Model):
    digest = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20)
    session_digest = models.CharField(max_length=64)
    expires_at = models.DateTimeField()


class CalendarEvent(models.Model):
    mount = models.ForeignKey(Mount, on_delete=models.PROTECT)
    external_id = models.CharField(max_length=255)
    title = models.CharField(max_length=500)
    starts_at = models.DateTimeField(null=True)
    ends_at = models.DateTimeField(null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    blocking = models.BooleanField(default=True)
    url = models.URLField(max_length=2000, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["mount", "external_id"], name="unique_event_occurrence"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        starts_at__isnull=False,
                        ends_at__gt=models.F("starts_at"),
                        start_date__isnull=True,
                        end_date__isnull=True,
                    )
                    | models.Q(
                        starts_at__isnull=True,
                        ends_at__isnull=True,
                        start_date__isnull=False,
                        end_date__gt=models.F("start_date"),
                    )
                ),
                name="event_valid_interval",
            ),
        ]
