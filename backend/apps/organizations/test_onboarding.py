import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.billing.tests import member_client
from apps.organizations.models import Organization, OrganizationMembership
from apps.properties.models import Property, Unit

pytestmark = pytest.mark.django_db
URL = "/api/v1/organizations/onboarding/"
PAYLOAD = {
    "business_name": "My property business",
    "email": "rent@example.com",
    "phone_number": "+260 971 234567",
    "property_name": "Garden Court",
    "property_type": "apartment",
    "address": "Plot 12, Lake Road",
    "town": "Lusaka",
    "unit_name": "Flat 1",
    "rent_amount": "3900.00",
}


def unassigned_client():
    user = get_user_model().objects.create_user(
        username="setup-user", password="SafeSetupPhrase27!"
    )
    client = APIClient()
    client.force_authenticate(user)
    return user, client


def test_new_user_creates_own_workspace_property_and_unit_once():
    user, client = unassigned_client()
    assert client.get(URL).json()["response_data"]["needs_setup"]
    response = client.post(URL, PAYLOAD, format="json")
    assert response.status_code == 201
    membership = OrganizationMembership.objects.get(user=user)
    assert membership.role == "landlord"
    assert str(membership.organization) == PAYLOAD["business_name"]
    assert Property.objects.get().organization == membership.organization
    assert Unit.objects.get().rent_amount == 3900
    data = response.json()["response_data"]
    assert not data["needs_setup"]
    assert [step["done"] for step in data["steps"]] == [True, True, False, False, False]
    assert client.post(URL, PAYLOAD, format="json").status_code == 400
    assert Organization.objects.count() == 1
    assert Property.objects.count() == Unit.objects.count() == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("business_name", ""),
        ("property_name", " "),
        ("address", ""),
        ("property_type", "fake"),
        ("rent_amount", "-1"),
        ("rent_amount", "NaN"),
        ("rent_amount", "2.123"),
        ("unit_name", "x" * 81),
        ("email", "invalid"),
        ("phone_number", "hello"),
    ],
)
def test_invalid_setup_is_atomic(field, value):
    _, client = unassigned_client()
    response = client.post(URL, {**PAYLOAD, field: value}, format="json")
    assert response.status_code == 400
    assert not Organization.objects.exists()
    assert not Property.objects.exists()
    assert not Unit.objects.exists()


@pytest.mark.parametrize("role", ["tenant"])
def test_only_landlords_can_change_workspace_in_setup(role):
    org = Organization.objects.create(name="Existing workspace")
    client = member_client(org, role, "setup-member")
    assert client.post(URL, PAYLOAD, format="json").status_code == 403
    org.refresh_from_db()
    assert not org.display_name
    assert not Property.objects.exists()
    if role == "tenant":
        assert client.get(URL).status_code == 403


def test_setup_does_not_accept_another_workspace_id():
    other = Organization.objects.create(name="Other workspace")
    _, client = unassigned_client()
    assert (
        client.post(
            URL, {**PAYLOAD, "organization": str(other.public_id), "role": "admin"}, format="json"
        ).status_code
        == 201
    )
    assert Property.objects.get().organization != other
    other.refresh_from_db()
    assert not other.display_name


def test_existing_owner_updates_own_empty_workspace():
    org = Organization.objects.create(name="Owner workspace")
    client = member_client(org, "landlord", "setup-owner")
    assert client.post(URL, PAYLOAD, format="json").status_code == 201
    assert Organization.objects.count() == 1
    org.refresh_from_db()
    assert org.display_name == PAYLOAD["business_name"]


def test_setup_requires_authentication():
    client = APIClient()
    assert client.get(URL).status_code in (401, 403)
    assert client.post(URL, PAYLOAD, format="json").status_code in (401, 403)


@pytest.mark.parametrize("role", ["tenant"])
def test_receipt_issuer_details_require_landlord(role):
    org = Organization.objects.create(name="Protected issuer")
    client = member_client(org, role, "issuer-member")
    response = client.patch(
        f"/api/v1/organizations/{org.public_id}/", {"display_name": "Forged issuer"}, format="json"
    )
    assert response.status_code == 403
    org.refresh_from_db()
    assert org.display_name == ""


def test_landlord_can_update_issuer_but_not_another_membership_as_tenant():
    org = Organization.objects.create(name="Owner issuer")
    client = member_client(org, "landlord", "issuer-owner")
    assert (
        client.patch(
            f"/api/v1/organizations/{org.public_id}/",
            {"display_name": "My business"},
            format="json",
        ).status_code
        == 200
    )
    other = Organization.objects.create(name="Viewer issuer")
    OrganizationMembership.objects.create(
        organization=other, user=client.handler._force_user, role="tenant"
    )
    assert (
        client.patch(
            f"/api/v1/organizations/{other.public_id}/",
            {"display_name": "Not my business"},
            format="json",
        ).status_code
        == 404
    )
