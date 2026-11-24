import pytest
from rest_framework.test import APIClient

from kiosk.models import KioskDevice
from planner.services import create_task

pytestmark = pytest.mark.django_db


def test_pairing_redaction_scope_and_revocation(client, user, settings):
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    user.date_order = "mdy"
    user.date_separator = "/"
    user.language = "pt-BR"
    user.save(update_fields=["date_order", "date_separator", "language"])
    create_task(user, {"title": "Visible", "notes": "Secret notes", "do_date": "2026-11-18"})
    device_client = APIClient()
    started = device_client.post("/api/v1/kiosk/pair/")
    assert started.status_code == 201
    pair = started.json()
    assert pair["expires_at"]
    pending = device_client.post("/api/v1/kiosk/pair/poll/", {"secret": pair["secret"]})
    assert pending.status_code == 202
    assert pending.json() == {"status": "pending"}
    approved = client.post(
        "/api/v1/kiosk/pair/approve/", {"code": pair["code"], "label": "Office TV"}
    )
    assert approved.status_code == 201
    claimed = device_client.post("/api/v1/kiosk/pair/poll/", {"secret": pair["secret"]})
    assert claimed.status_code == 200
    assert claimed.json()["expires_at"]
    token = claimed.json()["token"]
    claimed_again = device_client.post("/api/v1/kiosk/pair/poll/", {"secret": pair["secret"]})
    assert claimed_again.status_code == 400
    assert claimed_again.json() == ["Pairing expired or was already claimed. Start again."]
    invalid = device_client.post("/api/v1/kiosk/pair/poll/", {})
    assert invalid.status_code == 400
    assert isinstance(invalid.json()["secret"], list)
    device_client.credentials(HTTP_AUTHORIZATION="Device " + token)
    summary = device_client.get("/api/v1/kiosk/summary/")
    assert summary.status_code == 200
    assert summary.json()["date_order"] == "mdy"
    assert summary.json()["date_separator"] == "/"
    assert summary.json()["language"] == "pt-BR"
    assert "notes" not in str(summary.json())
    assert device_client.get("/api/v1/tasks/").status_code == 403
    assert device_client.post("/api/v1/tasks/", {"title": "Unauthorized"}).status_code == 403
    assert token not in str(KioskDevice.objects.values().first())
    assert client.post(f"/api/v1/kiosk/devices/{approved.json()['id']}/revoke/").status_code == 204
    assert device_client.get("/api/v1/kiosk/summary/").status_code == 401
