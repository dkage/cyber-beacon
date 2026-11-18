from django.db import transaction
from django.http import HttpResponseRedirect
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from jobs.queue import enqueue
from planner.serializers import TaskSerializer
from planner.services import lock_user

from . import providers, services
from .models import Mount, TaskSource
from .serializers import (
    BrowseQuerySerializer,
    ConnectionSerializer,
    CreateMountSerializer,
    ImportSerializer,
    MountSerializer,
    ProviderSerializer,
)


class OAuthStart(APIView):
    @extend_schema(request=ProviderSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        serializer = ProviderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"url": services.begin_oauth(request, serializer.validated_data["provider"])}
        )


class OAuthCallback(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(exclude=True)
    def get(self, request, provider):
        if provider not in {"notion", "google", "microsoft"}:
            raise ValidationError("Unknown Provider.")
        if request.query_params.get("error"):
            return HttpResponseRedirect("/connections?error=consent-denied")
        services.finish_oauth(
            request,
            provider,
            request.query_params.get("state", "")[:500],
            request.query_params.get("code", "")[:4000],
        )
        return HttpResponseRedirect("/connections?connected=1")


class ConnectionViewSet(viewsets.GenericViewSet):
    serializer_class = ConnectionSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        return (
            self.request.user.integrationconnection_set.all()
            .prefetch_related("mounts")
            .order_by("provider", "label", "pk")
        )

    def list(self, request):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    @extend_schema(request=None, responses={204: None})
    @action(detail=True, methods=["post"])
    def disconnect(self, request, pk=None):
        services.disconnect(request.user, self.get_object())
        return Response(status=204)

    @extend_schema(parameters=[BrowseQuerySerializer], responses=OpenApiTypes.OBJECT)
    @action(detail=True, methods=["get"])
    def resources(self, request, pk=None):
        query = BrowseQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(providers.resources(self.get_object(), **query.validated_data))

    @extend_schema(request=CreateMountSerializer, responses=MountSerializer)
    @action(detail=True, methods=["post"])
    def mounts(self, request, pk=None):
        connection = self.get_object()
        serializer = CreateMountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if connection.status != "active":
            raise ValidationError("Reconnect this Provider first.")
        with transaction.atomic():
            lock_user(request.user)
            connection.refresh_from_db(fields=["status"])
            if connection.status != "active":
                raise ValidationError("Reconnect this Provider first.")
            mount, _ = Mount.objects.get_or_create(
                connection=connection,
                external_id=data["external_id"],
                defaults={"label": data["label"]},
            )
            mount.enabled = True
            mount.save(update_fields=["enabled"])
        if connection.provider in {"google", "microsoft"}:
            transaction.on_commit(
                lambda: enqueue("integrations.services.sync_calendar", str(mount.pk))
            )
        return Response(MountSerializer(mount).data, status=201)


class MountViewSet(viewsets.GenericViewSet):
    serializer_class = MountSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        return Mount.objects.filter(connection__user=self.request.user).select_related("connection")

    @extend_schema(parameters=[BrowseQuerySerializer], responses=OpenApiTypes.OBJECT)
    @action(detail=True, methods=["get"])
    def browse(self, request, pk=None):
        mount = self.get_object()
        if mount.connection.provider != "notion" or not mount.enabled:
            raise ValidationError("Choose an enabled Notion Mount.")
        query = BrowseQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        result = providers.browse(
            mount, query.validated_data["cursor"], query.validated_data["query"]
        )
        rows = result.get("results", [])
        counts = {}
        for external_id in TaskSource.objects.filter(
            mount__connection=mount.connection,
            task__user=request.user,
            task__deleted_at=None,
            external_id__in=[row["id"] for row in rows],
        ).values_list("external_id", flat=True):
            counts[external_id] = counts.get(external_id, 0) + 1
        return Response(
            {
                "results": [
                    {
                        "id": row["id"],
                        "title": providers.notion_title(row),
                        "url": row.get("url", ""),
                        "imported_count": counts.get(row["id"], 0),
                    }
                    for row in rows
                ],
                "next_cursor": result.get("next_cursor"),
            }
        )

    @extend_schema(request=ImportSerializer, responses=TaskSerializer)
    @action(detail=True, methods=["post"], url_path="import")
    def import_record(self, request, pk=None):
        serializer = ImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        task = services.import_record(
            request.user, self.get_object(), str(data["external_id"]), data["do_date"], data["key"]
        )
        return Response(TaskSerializer(task).data, status=201)

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    @action(detail=True, methods=["post"])
    def refresh(self, request, pk=None):
        mount = self.get_object()
        if (
            mount.connection.provider not in {"google", "microsoft"}
            or mount.connection.status != "active"
        ):
            raise ValidationError("Choose an active Calendar Mount.")
        mount.enabled = True
        mount.save(update_fields=["enabled"])
        enqueue("integrations.services.sync_calendar", str(mount.pk))
        return Response({"status": "queued"}, status=202)
