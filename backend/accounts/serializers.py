from rest_framework import serializers

from .models import User, validate_timezone


class SettingsSerializer(serializers.ModelSerializer):
    timezone = serializers.CharField(validators=[validate_timezone])
    work_weekdays = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6), allow_empty=False, max_length=7
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "timezone",
            "work_start",
            "work_end",
            "work_weekdays",
            "date_order",
            "date_separator",
        ]
        read_only_fields = ["id", "email"]

    def validate(self, attrs):
        start = attrs.get("work_start", self.instance.work_start)
        end = attrs.get("work_end", self.instance.work_end)
        if end <= start:
            raise serializers.ValidationError(
                {"work_end": "Choose an end after the start on the same day."}
            )
        return attrs
