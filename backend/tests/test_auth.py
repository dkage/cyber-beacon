import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


def test_real_allauth_session_csrf_rotation_and_logout(user):
    client = Client(enforce_csrf_checks=True)
    token = client.get("/api/v1/csrf/").json()["csrf_token"]
    login = "/_allauth/browser/v1/auth/login"
    payload = {"email": user.email, "password": "test-password-982"}
    assert client.post(login, payload, content_type="application/json").status_code == 403
    response = client.post(login, payload, content_type="application/json", HTTP_X_CSRFTOKEN=token)
    assert response.status_code == 200
    assert response.cookies["sessionid"]["httponly"]
    assert (
        client.post(
            "/api/v1/tasks/", {"title": "CSRF protected"}, HTTP_X_CSRFTOKEN=token
        ).status_code
        == 403
    )
    rotated = client.get("/api/v1/csrf/").json()["csrf_token"]
    assert (
        client.post(
            "/api/v1/tasks/", {"title": "CSRF protected"}, HTTP_X_CSRFTOKEN=rotated
        ).status_code
        == 201
    )
    assert (
        client.delete("/_allauth/browser/v1/auth/session", HTTP_X_CSRFTOKEN=rotated).status_code
        == 401
    )
    assert client.get("/api/v1/tasks/").status_code == 403


def test_static_deep_link_and_missing_asset(settings, tmp_path):
    settings.FRONTEND_DIR = tmp_path
    (tmp_path / "index.html").write_text("<title>Beacon shell</title>")
    client = Client()
    assert client.get("/connections").status_code == 200
    assert client.get("/api/v1/missing/").status_code == 404
    assert client.get("/_app/missing.js").status_code == 404
