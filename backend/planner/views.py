from typing import cast

from django.db.models import QuerySet
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.models import User

from . import services
from .models import Task, TimeEntry
from .serializers import (
    ActivitySerializer,
    PreconditionErrorSerializer,
    ReorderSerializer,
    StartTimerSerializer,
    TaskListQuerySerializer,
    TaskSerializer,
    TimeEntrySerializer,
)


def precondition(request: Request) -> int | None:
    value = request.headers.get("If-Match")
    if value is None:
        return None
    try:
        if value != f'"{int(value.strip(chr(34)))}"':
            raise ValueError()
        return int(value.strip('"'))
    except ValueError as exc:
        from rest_framework.exceptions import ValidationError

        raise ValidationError({"If-Match": 'Expected "<integer version>".'}) from exc


class TaskViewSet(viewsets.GenericViewSet[Task]):
    lookup_value_regex = "[0-9a-f-]{36}"
    serializer_class = TaskSerializer
    queryset = Task.objects.none()

    def get_queryset(self) -> QuerySet[Task]:
        # The API requires an authenticated user via the default DRF permission.
        return Task.objects.filter(user=cast(User, self.request.user), deleted_at=None)

    @extend_schema(parameters=[TaskListQuerySerializer])
    def list(self, request: Request) -> Response:
        query = TaskListQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        tasks = Task.objects.filter(
            user=cast(User, request.user), deleted_at__isnull=not params["trash"]
        )
        if params["backlog"]:
            tasks = tasks.filter(do_date=None)
        elif "date" in params:
            tasks = tasks.filter(do_date=params["date"])
        page = self.paginate_queryset(tasks)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        task = self.get_object()
        return Response(self.get_serializer(task).data, headers={"ETag": f'"{task.version}"'})

    @extend_schema(responses={201: TaskSerializer})
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        completed = data.pop("completed", False)
        if completed:
            data["completed_at"] = timezone.now()
        task = services.create_task(request.user, data)
        return Response(self.get_serializer(task).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[OpenApiParameter("If-Match", str, OpenApiParameter.HEADER, required=True)]
    )
    def partial_update(self, request, pk=None):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        task = services.change_task(
            request.user, pk, dict(serializer.validated_data), precondition(request)
        )
        return Response(self.get_serializer(task).data, headers={"ETag": f'"{task.version}"'})

    @extend_schema(
        parameters=[OpenApiParameter("If-Match", str, OpenApiParameter.HEADER, required=True)],
        responses={204: None},
    )
    def destroy(self, request, pk=None):
        services.change_task(request.user, pk, {}, precondition(request), action="delete")
        return Response(status=204)

    @extend_schema(
        request=None,
        parameters=[OpenApiParameter("If-Match", str, OpenApiParameter.HEADER, required=True)],
        responses={
            200: TaskSerializer,
            400: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"If-Match": {"type": "string"}},
                    "required": ["If-Match"],
                },
                description="The If-Match header is malformed.",
            ),
            412: OpenApiResponse(PreconditionErrorSerializer, "The Task version is stale."),
            428: OpenApiResponse(PreconditionErrorSerializer, "The If-Match header is required."),
        },
    )
    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        task = services.change_task(request.user, pk, {}, precondition(request), action="restore")
        return Response(self.get_serializer(task).data)

    @extend_schema(responses=ActivitySerializer(many=True))
    @action(detail=True, methods=["get"])
    def activity(self, request, pk=None):
        return Response(ActivitySerializer(self.get_object().activity.all()[:500], many=True).data)

    @extend_schema(request=ReorderSerializer, responses=TaskSerializer(many=True))
    @action(detail=False, methods=["post"])
    def reorder(self, request):
        serializer = ReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tasks = services.reorder(
            request.user, serializer.validated_data["date"], serializer.validated_data["items"]
        )
        return Response(self.get_serializer(tasks, many=True).data)


class TimerViewSet(viewsets.GenericViewSet[TimeEntry]):
    lookup_value_regex = "[0-9a-f-]{36}"
    serializer_class = TimeEntrySerializer
    queryset = TimeEntry.objects.none()

    @extend_schema(responses=TimeEntrySerializer(allow_null=True))
    @action(detail=False, methods=["get"])
    def current(self, request):
        entry = TimeEntry.objects.filter(user=request.user, ended_at=None).first()
        return Response(self.get_serializer(entry).data if entry else None)

    @extend_schema(request=StartTimerSerializer)
    @action(detail=False, methods=["post"])
    def start(self, request):
        serializer = StartTimerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = services.start_timer(request.user, serializer.validated_data["task"])
        return Response(self.get_serializer(entry).data)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def stop(self, request, pk=None):
        entry = services.stop_timer(request.user, pk)
        return Response(self.get_serializer(entry).data)
