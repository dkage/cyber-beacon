from rest_framework import serializers

from accounts.models import DATE_ORDER_CHOICES, DATE_SEPARATOR_CHOICES, LANGUAGE_CHOICES
from planner.read_models import FreshnessSerializer


class PairingStartedSerializer(serializers.Serializer):
    code = serializers.CharField()
    secret = serializers.CharField()
    expires_at = serializers.DateTimeField()


class PairingPendingSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["pending"])


class PairingClaimedSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()


class KioskTaskSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    completed_at = serializers.DateTimeField(allow_null=True)
    estimated_minutes = serializers.IntegerField(allow_null=True)


class KioskEventSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    starts_at = serializers.DateTimeField(allow_null=True)
    ends_at = serializers.DateTimeField(allow_null=True)
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)


class KioskSummarySerializer(serializers.Serializer):
    date = serializers.DateField()
    timezone = serializers.CharField()
    date_order = serializers.ChoiceField(choices=DATE_ORDER_CHOICES)
    date_separator = serializers.ChoiceField(choices=DATE_SEPARATOR_CHOICES)
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, required=False)
    fetched_at = serializers.DateTimeField()
    tasks = KioskTaskSerializer(many=True)
    events = KioskEventSerializer(many=True)
    calendars = FreshnessSerializer(many=True)
    briefing = serializers.CharField()
