from unittest.mock import patch

import pytest

from apps.properties.models import Property

from .models import AuditEvent
from .support_test_utils import start

pytestmark = pytest.mark.django_db

def test_admin_crud_is_scoped_and_every_write_audited(context):
    client, user, org, other = context
    session = start(client, org)
    foreign = Property.objects.create(organization=other, name="Private", address="Plot 2")
    response = client.post(
        "/api/v1/properties/",
        {"name": "New home", "address": "Plot 1", "property_type": "house"},
        format="json",
        HTTP_X_REQUEST_ID="support-request-123",
    )
    assert response.status_code == 201, response.content
    public_id = response.json()["response_data"]["id"]
    prop = Property.objects.get(public_id=public_id)
    assert prop.organization == org
    assert (
        client.patch(
            f"/api/v1/properties/{public_id}/", {"name": "Edited"}, format="json"
        ).status_code
        == 200
    )
    assert client.get(f"/api/v1/properties/{foreign.public_id}/").status_code == 404
    assert (
        client.patch(
            f"/api/v1/properties/{foreign.public_id}/", {"name": "Leak"}, format="json"
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/properties/{foreign.public_id}/").status_code == 404
    assert len(client.get("/api/v1/properties/").json()["response_data"]) == 1
    assert client.delete(f"/api/v1/properties/{public_id}/").status_code == 204
    events = AuditEvent.objects.filter(action__startswith="support.")
    assert events.count() == 3
    for event in events:
        assert event.actor == user and event.organization == org
        assert event.resource_type == "properties.property" and event.resource_id == public_id
        assert event.metadata["support_session"] == str(session.public_id)
        assert event.metadata["reason"] == session.reason
    assert events.get(action="support.create").request_id == "support-request-123"
    foreign.refresh_from_db()
    assert foreign.name == "Private"



def test_settings_write_and_api_view_write_are_scoped_audited(context):
    client, _, org, other = context
    start(client, org)
    assert (
        client.patch(
            f"/api/v1/organizations/{org.public_id}/", {"display_name": "Supported"}, format="json"
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/organizations/{other.public_id}/", {"display_name": "Leak"}, format="json"
        ).status_code
        == 404
    )
    setup = {
        "business_name": "Supported",
        "property_name": "First house",
        "address": "Plot 1",
        "property_type": "house",
        "unit_name": "A1",
        "rent_amount": "5000.00",
    }
    assert client.post("/api/v1/organizations/onboarding/", setup, format="json").status_code == 201
    assert Property.objects.get().organization == org
    assert AuditEvent.objects.filter(action__startswith="support.").count() == 2
    event = AuditEvent.objects.get(resource_type="OnboardingView")
    assert event.resource_id == str(org.public_id)
    assert event.metadata["reason"] == "Beta onboarding call"



def test_audit_failure_rolls_back_business_write(context):
    client, _, org, _ = context
    start(client, org)
    with patch("apps.audit.middleware.record_event", side_effect=RuntimeError("Audit unavailable")):
        with pytest.raises(RuntimeError, match="Audit unavailable"):
            client.post(
                "/api/v1/properties/",
                {"name": "Must roll back", "address": "Plot 1", "property_type": "house"},
                format="json",
            )
    assert not Property.objects.exists()

