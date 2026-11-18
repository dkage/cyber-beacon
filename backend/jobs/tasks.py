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
            continue
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


def integration_tick():
    from integrations.models import Mount

    from .queue import enqueue

    now = timezone.now()
    # Move dispatch time forward in a transaction; missed dispatch is retried next minute.
    from django.db import transaction

    with transaction.atomic():
        mounts = Mount.objects.select_for_update(skip_locked=True).filter(
            enabled=True,
            connection__status="active",
            connection__provider__in=["google", "microsoft"],
            next_attempt_at__lte=now,
        )[:100]
        for mount in mounts:
            mount.next_attempt_at = now + timedelta(minutes=1)
            mount.save(update_fields=["next_attempt_at"])
            transaction.on_commit(
                lambda pk=str(mount.pk): enqueue("integrations.services.sync_calendar", pk)
            )
