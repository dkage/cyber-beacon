from django.utils import timezone
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from integrations.services import digest

from .models import KioskDevice


class KioskAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Device "):
            raise AuthenticationFailed("Pair this display to continue.")
        token = header[7:]
        device = (
            KioskDevice.objects.select_related("user")
            .filter(
                token_digest=digest(token),
                revoked_at=None,
                expires_at__gt=timezone.now(),
                user__is_active=True,
            )
            .first()
        )
        if not device:
            raise AuthenticationFailed(
                "Device access expired or was revoked. Pair this display again."
            )
        return device.user, device

    def authenticate_header(self, request):
        return "Device"


class KioskAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "kiosk.auth.KioskAuthentication"
    name = "deviceAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Device <opaque token>; read-only kiosk summary only.",
        }
