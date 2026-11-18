from zoneinfo import ZoneInfo

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import DATE_ORDER_CHOICES, DATE_SEPARATOR_CHOICES
from integrations.models import Mount
from integrations.serializers import CalendarEventSerializer
from integrations.services import events_for_day

from .day import capacity, time_totals
from .models import Task, TimeEntry
from .serializers import DayQuerySerializer, TaskSerializer, TimeEntrySerializer


class CapacitySerializer(serializers.Serializer):
    work_minutes = serializers.IntegerField()
    meeting_minutes = serializers.IntegerField()
    available_minutes = serializers.IntegerField()
    estimated_minutes = serializers.IntegerField()
    remaining_minutes = serializers.IntegerField()
    unestimated_tasks = serializers.IntegerField()


class FreshnessSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    label = serializers.CharField()
    last_succeeded_at = serializers.DateTimeField(allow_null=True)
    last_error = serializers.CharField()
    enabled = serializers.BooleanField()


class DaySerializer(serializers.Serializer):
    date = serializers.DateField()
    timezone = serializers.CharField()
    date_order = serializers.ChoiceField(choices=DATE_ORDER_CHOICES)
    date_separator = serializers.ChoiceField(choices=DATE_SEPARATOR_CHOICES)
    fetched_at = serializers.DateTimeField()
    tasks = TaskSerializer(many=True)
    events = CalendarEventSerializer(many=True)
    capacity = CapacitySerializer()
    task_actual_seconds = serializers.DictField(child=serializers.IntegerField())
    day_actual_seconds = serializers.IntegerField()
    timer = TimeEntrySerializer(allow_null=True)
    calendars = FreshnessSerializer(many=True)


def day_summary(user, day):
    events = list(events_for_day(user, day))
    tasks = list(
        Task.objects.filter(user=user, do_date=day, deleted_at=None).select_related(
            "source__mount__connection"
        )
    )
    totals, seconds = time_totals(user, day)
    timer = TimeEntry.objects.filter(user=user, ended_at=None).first()
    return {
        "date": day,
        "timezone": user.timezone,
        "date_order": user.date_order,
        "date_separator": user.date_separator,
        "fetched_at": timezone.now(),
        "tasks": tasks,
        "events": events,
        "capacity": capacity(user, day, events),
        "task_actual_seconds": totals,
        "day_actual_seconds": seconds,
        "timer": timer,
        "calendars": list(
            Mount.objects.filter(
                connection__user=user, connection__provider__in=["google", "microsoft"]
            ).values("id", "label", "last_succeeded_at", "last_error", "enabled")
        ),
    }


class DayView(APIView):
    @extend_schema(parameters=[DayQuerySerializer], responses=DaySerializer)
    def get(self, request):
        query = DayQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        day = query.validated_data.get(
            "date", timezone.now().astimezone(ZoneInfo(request.user.timezone)).date()
        )
        return Response(DaySerializer(day_summary(request.user, day)).data)
