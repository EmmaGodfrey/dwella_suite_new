import pytest
from django.contrib.auth import get_user_model

from apps.common.permissions import get_user_access
from apps.organizations.models import OrganizationMembership

pytestmark = pytest.mark.django_db


def test_suspended_workspace_blocks_member_and_support_portfolio_access(context):
    client, _, org, _ = context
    session = client.post("/api/v1/platform/support-sessions/", {
        "organization": str(org.public_id), "reason": "Reviewing support request",
    }, format="json")
    assert session.status_code == 201
    org.is_active = False
    org.save()
    assert client.get(
        "/api/v1/properties/", HTTP_X_DWELLA_WORKSPACE=str(org.public_id),
    ).status_code == 403
    assert client.post("/api/v1/platform/support-sessions/", {
        "organization": str(org.public_id), "reason": "Reviewing support request",
    }, format="json").status_code == 400
    owner = get_user_model().objects.create_user(username="suspended-owner")
    OrganizationMembership.objects.create(user=owner, organization=org, role="landlord")
    access = get_user_access(owner)
    assert access["workspace_suspended"] and not access["can_manage_organization"]
    assert not access["can_view_portfolio"]
    client.force_authenticate(owner)
    assert client.get("/api/v1/accounts/me/").status_code == 200
    assert client.get("/api/v1/properties/").status_code == 403
    assert client.patch(
        f"/api/v1/organizations/{org.public_id}/", {"is_active": True}, format="json",
    ).status_code == 403
    org.refresh_from_db()
    assert not org.is_active
