from django.conf import settings
from django.db import models
from django.utils import timezone


class JobRun(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(max_length=40)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True)
    outcome = models.CharField(max_length=30, default="started")
    message = models.CharField(max_length=500, blank=True)
    counts = models.JSONField(default=dict)
