from django.db import transaction
from django.http import HttpResponseRedirect
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated, Throttled, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from jobs.queue import enqueue
from planner.serializers import TaskSerializer
from planner.services import lock_user

from . import providers, services
from .models import IntegrationConnection, Mount, TaskSource
from .serializers import (
    BrowsePageSerializer,
    BrowseQuerySerializer,
    ConnectionSerializer,
    CreateMountSerializer,
    ImportSerializer,
    MountSerializer,
    OAuthRedirectSerializer,
    ProviderSerializer,
    ResourcePageSerializer,
)


class OAuthStart(APIView):
    @extend_schema(request=ProviderSerializer, responses=OAuthRedirectSerializer)
    def post(self, request):
        serializer = ProviderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.session.session_key:
            request.session.save()
        return Response(
            {
                "url": services.begin_oauth(
                    request.user, request.session.session_key, serializer.validated_data["provider"]
                )
            }
        )


class OAuthCallback(APIView):
    permission_classes = [IsAuthenticated]

    def handle_exception(self, exc):
        if isinstance(exc, NotAuthenticated):
            return HttpResponseRedirect("/login?error=connection_session")
        return super().handle_exception(exc)

    @extend_schema(exclude=True)
    def get(self, request, provider):
        if provider not in {"notion", "google", "microsoft", "github"}:
            return HttpResponseRedirect("/connections?error=unknown_provider")
        if request.query_params.get("error"):
            return HttpResponseRedirect("/connections?error=consent-denied")
        try:
            services.finish_oauth(
                request.user,
                request.session.session_key,
                provider,
                request.query_params.get("state", "")[:500],
                request.query_params.get("code", "")[:4000],
            )
        except ValidationError:
            return HttpResponseRedirect("/connections?error=connection_expired")
        except providers.ProviderError as exc:
            code = exc.get_codes()
            if code not in ("reconnect_provider", "throttled"):
                code = "provider_error"
            return HttpResponseRedirect(f"/connections?error={code}")
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

    @extend_schema(parameters=[BrowseQuerySerializer], responses=ResourcePageSerializer)
    @action(detail=True, methods=["get"])
    def resources(self, request, pk=None):
        query = BrowseQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(providers.resources(self.get_object(), **query.validated_data))

    @extend_schema(request=CreateMountSerializer, responses={201: MountSerializer})
    @action(detail=True, methods=["post"])
    def mounts(self, request, pk=None):
        connection = self.get_object()
        serializer = CreateMountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if connection.status != "active":
            raise ValidationError("Reconnect this Provider first.", code="reconnect_provider")
        with transaction.atomic():
            lock_user(request.user)
            connection.refresh_from_db(fields=["status"])
            if connection.status != "active":
                raise ValidationError("Reconnect this Provider first.", code="reconnect_provider")
            mount, _ = Mount.objects.get_or_create(
                connection=connection,
                external_id=data["external_id"],
                defaults={"label": data["label"]},
            )
            mount.enabled = True
            mount.save(update_fields=["enabled"])
        if providers.supports(connection.provider, "calendar"):
            transaction.on_commit(
                lambda: enqueue("integrations.services.sync_calendar", str(mount.pk))
            )
        return Response(MountSerializer(mount).data, status=201)


class MountViewSet(viewsets.GenericViewSet):
    serializer_class = MountSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        return Mount.objects.filter(connection__user=self.request.user).select_related("connection")

    @extend_schema(parameters=[BrowseQuerySerializer], responses=BrowsePageSerializer)
    @action(detail=True, methods=["get"])
    def browse(self, request, pk=None):
        mount = self.get_object()
        if not providers.supports(mount.connection.provider, "worksheet") or not mount.enabled:
            raise ValidationError(
                "Choose an enabled worksheet source Mount.", code="choose_worksheet_source"
            )
        query = BrowseQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        result = providers.browse(
            mount, query.validated_data["cursor"], query.validated_data["query"]
        )
        rows = result.get("results", [])
        external_ids = [
            str(row["id"]) if mount.connection.provider == "notion" else str(row["number"])
            for row in rows
        ]
        counts = {}
        for external_id in TaskSource.objects.filter(
            mount=mount,
            task__user=request.user,
            task__deleted_at=None,
            external_id__in=external_ids,
        ).values_list("external_id", flat=True):
            counts[external_id] = counts.get(external_id, 0) + 1
        return Response(
            {
                "results": [
                    {
                        "id": str(row["id"])
                        if mount.connection.provider == "notion"
                        else str(row["number"]),
                        "title": (
                            providers.notion_title(row, fallback="")
                            if mount.connection.provider == "notion"
                            else f"#{row['number']} {row['title']}"
                            if row.get("title")
                            else ""
                        ),
                        "url": row.get("url")
                        if mount.connection.provider == "notion"
                        else row.get("html_url", ""),
                        "imported_count": counts.get(
                            str(row["id"])
                            if mount.connection.provider == "notion"
                            else str(row["number"]),
                            0,
                        ),
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
            request.user, self.get_object(), data["external_id"], data["do_date"], data["key"]
        )
        return Response(TaskSerializer(task).data, status=201)

    @extend_schema(
        request=None,
        responses={
            202: OpenApiTypes.OBJECT,
            400: OpenApiResponse(
                response={"type": "array", "items": {"type": "string"}},
                description="The Mount is ineligible or its Connection changed.",
            ),
            429: OpenApiTypes.OBJECT,
        },
        parameters=[
            OpenApiParameter(
                "Retry-After",
                int,
                OpenApiParameter.HEADER,
                response=[429],
                description="Seconds until the calendar can be refreshed.",
            ),
        ],
    )
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def refresh(self, request, pk=None):
        mount = self.get_object()
        # Disconnect takes the same locks in this order.
        connection = (
            IntegrationConnection.objects.select_for_update()
            .only("provider", "status", "auth_version")
            .get(pk=mount.connection_id)
        )
        if not providers.supports(connection.provider, "calendar") or connection.status != "active":
            raise ValidationError("Choose an active Calendar Mount.", code="choose_active_calendar")
        if connection.auth_version != mount.connection.auth_version:
            raise ValidationError("The Connection changed. Refresh and try again.", code="conflict")
        mount.refresh_from_db(
            fields=["rate_limited_until"], from_queryset=Mount.objects.select_for_update()
        )
        if mount.rate_limited_until:
            wait = (mount.rate_limited_until - timezone.now()).total_seconds()
            if wait > 0:
                raise Throttled(wait=wait, detail="The Provider is rate limiting this calendar.")
        mount.enabled = True
        mount.save(update_fields=["enabled"])
        transaction.on_commit(lambda: enqueue("integrations.services.sync_calendar", str(mount.pk)))
        return Response({"status": "queued"}, status=202)
