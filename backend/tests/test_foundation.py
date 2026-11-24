from django.conf import settings
from django.test import Client


def test_cluster_retry_exceeds_timeout():
    primary = settings.Q_CLUSTER
    for cluster in [primary, *primary["ALT_CLUSTERS"].values()]:
        assert cluster["retry"] > cluster["timeout"]


def test_csrf_bootstrap():
    response = Client(enforce_csrf_checks=True).get("/api/v1/csrf/")
    assert response.status_code == 200
    assert response.json()["csrf_token"]
    assert "csrftoken" in response.cookies


def test_user_language_defaults_to_english_and_persists_supported_values(client, user):
    path = "/api/v1/settings/"
    assert client.get(path).json()["language"] == "en"
    for language in ("pt-BR", "es", "en"):
        response = client.patch(path, {"language": language}, format="json")
        assert response.status_code == 200
        assert response.json()["language"] == language
        user.refresh_from_db()
        assert user.language == language
    invalid = client.patch(path, {"language": "pt"}, format="json")
    assert invalid.status_code == 400
    assert invalid["X-Beacon-Error-Code"] == "invalid_choice"
    assert "language" in invalid.json()
    invalid_hours = client.patch(path, {"work_start": "18:00", "work_end": "17:00"}, format="json")
    assert invalid_hours["X-Beacon-Error-Code"] == "invalid_work_hours"
    invalid_timezone = client.patch(path, {"timezone": "Invalid/Zone"}, format="json")
    assert invalid_timezone["X-Beacon-Error-Code"] == "invalid_timezone"
    assert client.get(path).json()["language"] == "en"


def test_user_date_format_preferences_are_saved_and_validated(client, user):
    initial = client.get("/api/v1/settings/")
    assert initial.status_code == 200
    assert initial.json()["date_order"] == "ymd"
    assert initial.json()["date_separator"] == "-"

    updated = client.patch(
        "/api/v1/settings/",
        {"date_order": "dmy", "date_separator": "/"},
        format="json",
    )
    assert updated.status_code == 200
    assert updated.json()["date_order"] == "dmy"
    assert updated.json()["date_separator"] == "/"

    user.refresh_from_db()
    persisted = client.get("/api/v1/settings/").json()
    assert persisted["date_order"] == "dmy"
    assert persisted["date_separator"] == "/"
    day = client.get("/api/v1/day/")
    assert day.json()["date_order"] == "dmy"
    assert day.json()["date_separator"] == "/"

    invalid = client.patch(
        "/api/v1/settings/", {"date_order": "foo", "date_separator": "."}, format="json"
    )
    assert invalid.status_code == 400
