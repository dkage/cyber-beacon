from typing import cast

from rest_framework import serializers

from .models import Task, TaskActivity, TimeEntry


class PreconditionErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class SourcePreviewSerializer(serializers.Serializer):
    url = serializers.URLField()
    raw = serializers.JSONField()
    imported_at = serializers.DateTimeField()
    provider = serializers.CharField(source="mount.connection.provider")


class TaskSerializer(serializers.ModelSerializer[Task]):
    # DRF collects these declared fields before using Field.source and Field.parent.
    source = SourcePreviewSerializer(read_only=True, allow_null=True)  # type: ignore[assignment]
    completed = serializers.BooleanField(write_only=True, required=False)
    parent = serializers.PrimaryKeyRelatedField(  # type: ignore[assignment]
        queryset=Task.objects.none(), allow_null=True, required=False
    )

    class Meta:
        model = Task
        fields = [
            "source",
            "id",
            "parent",
            "title",
            "notes",
            "do_date",
            "due_date",
            "start_date",
            "priority",
            "estimated_minutes",
            "position",
            "completed_at",
            "completed",
            "version",
            "deleted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "position",
            "completed_at",
            "version",
            "deleted_at",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"priority": {"max_value": 5}, "estimated_minutes": {"max_value": 10080}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            parent = cast(serializers.PrimaryKeyRelatedField[Task], self.fields["parent"])
            parent.queryset = Task.objects.filter(user=request.user, deleted_at=None)


class ActivitySerializer(serializers.ModelSerializer[TaskActivity]):
    class Meta:
        model = TaskActivity
        fields = ["id", "kind", "occurred_at", "payload"]


class TimeEntrySerializer(serializers.ModelSerializer[TimeEntry]):
    class Meta:
        model = TimeEntry
        fields = ["id", "task", "started_at", "ended_at"]
        read_only_fields = fields


class DayQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)


class TaskListQuerySerializer(DayQuerySerializer):
    backlog = serializers.BooleanField(required=False, default=False)
    trash = serializers.BooleanField(required=False, default=False)


class OrderItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    version = serializers.IntegerField(min_value=1)


class ReorderSerializer(serializers.Serializer):
    date = serializers.DateField()
    # DRF forwards max_length to its ListSerializer when many=True.
    items = OrderItemSerializer(many=True, max_length=1000)  # type: ignore[call-arg]


class StartTimerSerializer(serializers.Serializer):
    task = serializers.UUIDField()
