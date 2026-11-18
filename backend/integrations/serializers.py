from rest_framework import serializers

from .models import CalendarEvent, IntegrationConnection, Mount


class MountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mount
        fields = [
            "id",
            "connection",
            "external_id",
            "label",
            "enabled",
            "last_succeeded_at",
            "last_error",
            "consecutive_failures",
        ]
        read_only_fields = fields


class ConnectionSerializer(serializers.ModelSerializer):
    mounts = MountSerializer(many=True, read_only=True)

    class Meta:
        model = IntegrationConnection
        fields = ["id", "provider", "label", "status", "last_error", "mounts"]
        read_only_fields = fields


class ProviderSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=["notion", "google"])


class BrowseQuerySerializer(serializers.Serializer):
    cursor = serializers.CharField(required=False, default="", max_length=2000, allow_blank=True)
    query = serializers.CharField(required=False, default="", max_length=200, allow_blank=True)


class CreateMountSerializer(serializers.Serializer):
    external_id = serializers.CharField(max_length=255)
    label = serializers.CharField(max_length=255)


class ImportSerializer(serializers.Serializer):
    external_id = serializers.UUIDField()
    do_date = serializers.DateField(required=False, allow_null=True, default=None)
    key = serializers.UUIDField()


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = [
            "id",
            "mount",
            "title",
            "starts_at",
            "ends_at",
            "start_date",
            "end_date",
            "blocking",
            "url",
        ]
