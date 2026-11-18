from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from planner.services import carry_forward

from .models import JobRun


def daily_tick():
    for user in get_user_model().objects.filter(is_active=True).iterator():
        run = JobRun.objects.create(user=user, kind="carry_forward")
        try:
            count = carry_forward(user)
        except Exception:
            run.outcome = "failed"
            run.message = "Carry-forward failed. Check server logs and retry."
            run.ended_at = timezone.now()
            run.save()
            raise
        run.counts = {"carried_forward": count}
        run.outcome = "success"
        run.ended_at = timezone.now()
        run.save()
    JobRun.objects.filter(started_at__lt=timezone.now() - timedelta(days=30)).delete()
    JobRun.objects.filter(
        outcome="started", started_at__lt=timezone.now() - timedelta(minutes=5)
    ).update(
        outcome="lost",
        ended_at=timezone.now(),
        message="Worker stopped before recording an outcome.",
    )
