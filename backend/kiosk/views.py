import secrets
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from integrations.services import digest
from planner.read_models import DaySerializer, day_summary

from .auth import KioskAuthentication
from .models import DevicePairing, KioskDevice


class PairingThrottle(AnonRateThrottle):
    rate = "30/min"


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = KioskDevice
        fields = ["id", "label", "created_at", "expires_at", "revoked_at"]


class ApproveSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=8, max_length=8)
    label = serializers.CharField(max_length=100)


class PollSerializer(serializers.Serializer):
    secret = serializers.CharField(min_length=40, max_length=100)


class PairStart(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PairingThrottle]

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        code = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(8))
        secret = secrets.token_urlsafe(32)
        expiry = timezone.now() + timedelta(minutes=10)
        DevicePairing.objects.filter(expires_at__lt=timezone.now()).delete()
        DevicePairing.objects.create(
            secret_digest=digest(secret), code_digest=digest(code), expires_at=expiry
        )
        return Response({"code": code, "secret": secret, "expires_at": expiry}, status=201)


class PairApprove(APIView):
    @extend_schema(request=ApproveSerializer, responses=DeviceSerializer)
    @transaction.atomic
    def post(self, request):
        serializer = ApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        pairing = (
            DevicePairing.objects.select_for_update()
            .filter(
                code_digest=digest(data["code"].upper()), expires_at__gt=timezone.now(), device=None
            )
            .first()
        )
        if not pairing:
            raise ValidationError({"code": "Code expired or was already approved."})
        device = KioskDevice.objects.create(
            user=request.user, label=data["label"], expires_at=timezone.now() + timedelta(days=90)
        )
        pairing.device = device
        pairing.save(update_fields=["device"])
        return Response(DeviceSerializer(device).data, status=201)


class PairPoll(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PairingThrottle]

    @extend_schema(request=PollSerializer, responses=OpenApiTypes.OBJECT)
    @transaction.atomic
    def post(self, request):
        serializer = PollSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pairing = (
            DevicePairing.objects.select_for_update(of=("self",))
            .select_related("device")
            .filter(
                secret_digest=digest(serializer.validated_data["secret"]),
                expires_at__gt=timezone.now(),
                claimed=False,
            )
            .first()
        )
        if not pairing:
            raise ValidationError("Pairing expired or was already claimed. Start again.")
        if not pairing.device:
            return Response({"status": "pending"}, status=202)
        if pairing.device.revoked_at:
            raise ValidationError("Device was revoked. Start again.")
        token = secrets.token_urlsafe(48)
        pairing.device.token_digest = digest(token)
        pairing.device.save(update_fields=["token_digest"])
        pairing.claimed = True
        pairing.save(update_fields=["claimed"])
        return Response({"token": token, "expires_at": pairing.device.expires_at})


class Devices(generics.ListAPIView):
    serializer_class = DeviceSerializer
    pagination_class = None

    def get_queryset(self):
        return KioskDevice.objects.filter(user=self.request.user).order_by("-created_at")


class RevokeDevice(APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request, device_id):
        from django.shortcuts import get_object_or_404

        device = get_object_or_404(KioskDevice, pk=device_id, user=request.user)
        device.revoked_at = timezone.now()
        device.token_digest = None
        device.save(update_fields=["revoked_at", "token_digest"])
        return Response(status=204)


class KioskSummary(APIView):
    authentication_classes = [KioskAuthentication]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        day = timezone.now().astimezone(ZoneInfo(request.user.timezone)).date()
        full = DaySerializer(day_summary(request.user, day)).data
        return Response(
            {
                "date": day,
                "timezone": request.user.timezone,
                "fetched_at": full["fetched_at"],
                "tasks": [
                    {key: task[key] for key in ["id", "title", "completed_at", "estimated_minutes"]}
                    for task in full["tasks"]
                ],
                "events": [
                    {
                        key: event[key]
                        for key in ["id", "title", "starts_at", "ends_at", "start_date", "end_date"]
                    }
                    for event in full["events"]
                ],
                "calendars": full["calendars"],
                "briefing": "Briefing will arrive in a later release.",
            },
            headers={"Cache-Control": "no-store"},
        )
