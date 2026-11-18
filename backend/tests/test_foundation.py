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
