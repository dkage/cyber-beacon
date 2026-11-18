import pytest
from rest_framework.test import APIClient

from kiosk.models import KioskDevice
from planner.services import create_task

pytestmark = pytest.mark.django_db


def test_pairing_redaction_scope_and_revocation(client, user, settings):
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    user.date_order = "mdy"
    user.date_separator = "/"
    user.save(update_fields=["date_order", "date_separator"])
    create_task(user, {"title": "Visible", "notes": "Secret notes", "do_date": "2026-11-18"})
    device_client = APIClient()
    pair = device_client.post("/api/v1/kiosk/pair/").json()
    assert (
        device_client.post("/api/v1/kiosk/pair/poll/", {"secret": pair["secret"]}).status_code
        == 202
    )
    approved = client.post(
        "/api/v1/kiosk/pair/approve/", {"code": pair["code"], "label": "Office TV"}
    )
    assert approved.status_code == 201
    token = device_client.post("/api/v1/kiosk/pair/poll/", {"secret": pair["secret"]}).json()[
        "token"
    ]
    assert (
        device_client.post("/api/v1/kiosk/pair/poll/", {"secret": pair["secret"]}).status_code
        == 400
    )
    device_client.credentials(HTTP_AUTHORIZATION="Device " + token)
    summary = device_client.get("/api/v1/kiosk/summary/")
    assert summary.status_code == 200
    assert summary.json()["date_order"] == "mdy"
    assert summary.json()["date_separator"] == "/"
    assert "notes" not in str(summary.json())
    assert device_client.get("/api/v1/tasks/").status_code == 403
    assert device_client.post("/api/v1/tasks/", {"title": "Unauthorized"}).status_code == 403
    assert token not in str(KioskDevice.objects.values().first())
    assert client.post(f"/api/v1/kiosk/devices/{approved.json()['id']}/revoke/").status_code == 204
    assert device_client.get("/api/v1/kiosk/summary/").status_code == 401
