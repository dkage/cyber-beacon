import json

import pytest

pytestmark = pytest.mark.django_db


def test_api_schema_describes_integration_and_kiosk_contracts(client):
    response = client.get("/api/v1/", HTTP_ACCEPT="application/vnd.oai.openapi+json")
    schema = json.loads(response.content)
    paths = schema["paths"]

    browse = paths["/api/v1/integrations/mounts/{id}/browse/"]["get"]
    assert (
        browse["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/BrowsePage"
    )

    resources = paths["/api/v1/integrations/connections/{id}/resources/"]["get"]
    assert (
        resources["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ResourcePage"
    )

    mount_create = paths["/api/v1/integrations/connections/{id}/mounts/"]["post"]
    assert "201" in mount_create["responses"]
    assert "200" not in mount_create["responses"]

    restore = paths["/api/v1/tasks/{id}/restore/"]["post"]
    assert any(
        parameter["name"] == "If-Match" and parameter["in"] == "header" and parameter["required"]
        for parameter in restore["parameters"]
    )

    kiosk = paths["/api/v1/kiosk/summary/"]["get"]
    assert (
        kiosk["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/KioskSummary"
    )
