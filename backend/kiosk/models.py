import uuid

from django.conf import settings
from django.db import models


class KioskDevice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    label = models.CharField(max_length=100)
    token_digest = models.CharField(max_length=64, unique=True, null=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DevicePairing(models.Model):
    secret_digest = models.CharField(max_length=64, primary_key=True)
    code_digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    device = models.OneToOneField(KioskDevice, null=True, on_delete=models.CASCADE)
    claimed = models.BooleanField(default=False)
