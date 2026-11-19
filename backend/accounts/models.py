from datetime import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

DATE_ORDER_CHOICES = [
    ("ymd", "Year, month, day"),
    ("dmy", "Day, month, year"),
    ("mdy", "Month, day, year"),
]
DATE_SEPARATOR_CHOICES = [("-", "Hyphen (-)"), ("/", "Slash (/)")]


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
    work_start = models.TimeField(default=time(9))
    work_end = models.TimeField(default=time(17))
    work_weekdays = models.JSONField(default=list)
    date_order = models.CharField(max_length=3, choices=DATE_ORDER_CHOICES, default="ymd")
    date_separator = models.CharField(max_length=1, choices=DATE_SEPARATOR_CHOICES, default="-")
