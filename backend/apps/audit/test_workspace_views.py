
import pytest
from django.contrib.auth import get_user_model

from apps.organizations.models import Organization, OrganizationMembership

from .models import AuditEvent
from .support_test_utils import LANDLORD_URLS, start

pytestmark = pytest.mark.django_db

@pytest.mark.parametrize("url", LANDLORD_URLS)
def test_admin_must_choose_workspace(context, url):
    client, _, _, _ = context
    response = client.get(url)
    assert response.status_code == 400
    assert "Choose a workspace first" in response.json()["response_message"]



@pytest.mark.parametrize("url", LANDLORD_URLS)
def test_acting_admin_can_read_each_scoped_surface(context, url):
    client, _, org, _ = context
    start(client, org)
    response = client.get(url)
    assert response.status_code == 200, response.content



def test_support_owner_access_ignores_admin_personal_tenant_membership(context):
    client, user, org, other = context
    OrganizationMembership.objects.create(user=user, organization=other, role="tenant")
    start(client, org)
    response = client.get("/api/v1/organizations/onboarding/")
    assert response.status_code == 200
    assert response.json()["response_data"]["can_setup"] is True
    assert response.json()["response_data"]["business_name"] == str(org)



def test_support_session_cannot_create_a_different_workspace(context):
    client, user, org, _ = context
    start(client, org)
    response = client.post(
        "/api/v1/organizations/", {"name": "Outside selected scope"}, format="json"
    )
    assert response.status_code == 403
    assert Organization.objects.count() == 2
    assert not OrganizationMembership.objects.filter(user=user).exists()
    assert not AuditEvent.objects.filter(action="support.create").exists()
    assert client.delete(f"/api/v1/organizations/{org.public_id}/").status_code == 403
    assert Organization.objects.filter(pk=org.pk).exists()



def test_existing_landlord_can_read_and_update_second_membership_workspace(context):
    client, _, org, other = context
    landlord = get_user_model().objects.create_user(username="multi-workspace-owner")
    OrganizationMembership.objects.create(user=landlord, organization=org, role="owner")
    OrganizationMembership.objects.create(user=landlord, organization=other, role="owner")
    client.force_authenticate(landlord)
    assert len(client.get("/api/v1/organizations/").json()["response_data"]) == 2
    assert client.get(f"/api/v1/organizations/{other.public_id}/").status_code == 200
    assert (
        client.patch(
            f"/api/v1/organizations/{other.public_id}/",
            {"display_name": "Second owned workspace"},
            format="json",
        ).status_code
        == 200
    )
    foreign = Organization.objects.create(name="Unrelated workspace")
    assert client.get(f"/api/v1/organizations/{foreign.public_id}/").status_code == 404
