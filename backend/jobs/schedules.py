def ensure_schedules():
    from django_q.models import Schedule

    Schedule.objects.update_or_create(
        name="beacon-daily-tick",
        defaults={
            "func": "jobs.tasks.daily_tick",
            "schedule_type": Schedule.MINUTES,
            "minutes": 1,
            "repeats": -1,
            "cluster": "default",
        },
    )

    Schedule.objects.update_or_create(
        name="beacon-integration-tick",
        defaults={
            "func": "jobs.tasks.integration_tick",
            "schedule_type": Schedule.MINUTES,
            "minutes": 1,
            "repeats": -1,
            "cluster": "default",
        },
    )
