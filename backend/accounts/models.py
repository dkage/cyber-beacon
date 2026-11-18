from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


def validate_timezone(value):
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValidationError("Use an IANA timezone such as America/Sao_Paulo.") from exc


class User(AbstractUser):
    email = models.EmailField(unique=True)
    timezone = models.CharField(
        max_length=64, default="America/Sao_Paulo", validators=[validate_timezone]
    )
    work_start = models.TimeField(default="09:00")
    work_end = models.TimeField(default="17:00")
    work_weekdays = models.JSONField(default=list)
