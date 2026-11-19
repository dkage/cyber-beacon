from django.core.management.base import BaseCommand

from jobs.schedules import ensure_schedules


class Command(BaseCommand):
    def handle(self, *args, **options):
        ensure_schedules()
