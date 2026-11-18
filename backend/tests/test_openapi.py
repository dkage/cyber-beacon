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
    for code in ("412", "428"):
        assert (
            restore["responses"][code]["content"]["application/json"]["schema"]["$ref"]
            == "#/components/schemas/PreconditionError"
        )
    restore_error = restore["responses"]["400"]["content"]["application/json"]["schema"]
    assert restore_error["required"] == ["If-Match"]

    pair_start = paths["/api/v1/kiosk/pair/"]["post"]["responses"]
    assert (
        pair_start["201"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/PairingStarted"
    )
    pair_poll = paths["/api/v1/kiosk/pair/poll/"]["post"]["responses"]
    assert (
        pair_poll["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/PairingClaimed"
    )
    assert (
        pair_poll["202"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/PairingPending"
    )
    poll_error = pair_poll["400"]["content"]["application/json"]["schema"]
    assert {"type": "array", "items": {"type": "string"}} in poll_error["anyOf"]

    kiosk = paths["/api/v1/kiosk/summary/"]["get"]
    assert (
        kiosk["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/KioskSummary"
    )
