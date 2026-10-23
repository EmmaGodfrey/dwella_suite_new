import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.leases.models import Lease
from apps.organizations.models import Organization, OrganizationMembership
from apps.properties.models import Property, Unit

from .models import Tenant
from .phone import normalize_phone_number

User = get_user_model()


def member_client(organization, role, username):
    user = User.objects.create_user(username=username, password="StrongerPass123")
    OrganizationMembership.objects.create(organization=organization, user=user, role=role)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def make_unit(organization, name="1A", rent="3900.00", property_name="Mutendere Court"):
    property_obj, _ = Property.objects.get_or_create(
        organization=organization,
        name=property_name,
        defaults={"property_type": "apartment", "address": "Plot 4471"},
    )
    return Unit.objects.create(
        organization=organization, property=property_obj, name=name, rent_amount=rent
    )


@pytest.fixture
def org():
    return Organization.objects.create(name="Kafue Ridge Properties")


@pytest.fixture
def manager(org):
    return member_client(org, OrganizationMembership.Role.LANDLORD, "manager")


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("0971234567", "+260971234567"),
        ("971234567", "+260971234567"),
        ("+260 97 123 4567", "+260971234567"),
        ("260971234567", "+260971234567"),
        ("00260971234567", "+260971234567"),
        ("+44 20 7946 0958", "+442079460958"),
        ("097123", None),
        ("+2609712345", None),
        ("not a number", None),
        ("", None),
    ],
)
def test_normalize_phone_number(raw, expected):
    assert normalize_phone_number(raw) == expected


@pytest.mark.django_db
def test_manager_creates_tenant_with_normalized_phone(manager, org):
    response = manager.post(
        "/api/v1/tenants/",
        {
            "full_name": "  Bwalya   Kasonde ",
            "phone_number": "097 551 2208",
            "email": "Bwalya.K@Outlook.com",
        },
        format="json",
    )
    assert response.status_code == 201
    data = response.json()["response_data"]
    assert data["full_name"] == "Bwalya Kasonde"
    assert data["phone_number"] == "+260975512208"
    assert data["email"] == "bwalya.k@outlook.com"
    assert data["status"] == "applicant"
    assert data["current_lease"] is None
    assert Tenant.objects.get(public_id=data["id"]).organization == org


@pytest.mark.django_db
def test_tenant_with_lease_is_created_together_and_activated(manager, org):
    unit = make_unit(org)
    response = manager.post(
        "/api/v1/tenants/",
        {
            "full_name": "Chanda Mwila",
            "phone_number": "0974123381",
            "lease": {
                "unit": str(unit.public_id),
                "start_date": "2026-11-01",
                "end_date": "2027-10-31",
                "deposit_amount": "7800.00",
                "activate": True,
            },
        },
        format="json",
    )
    assert response.status_code == 201
    data = response.json()["response_data"]
    assert data["status"] == "active"
    lease = data["current_lease"]
    assert lease["reference"] == "LSE-0001"
    assert lease["monthly_rent"] == "3900.00"  # defaulted from the unit
    assert lease["unit_name"] == "1A"
    unit.refresh_from_db()
    assert unit.occupancy_status == "occupied"


@pytest.mark.django_db
def test_invalid_lease_rolls_back_the_new_tenant(manager, org):
    unit = make_unit(org)
    response = manager.post(
        "/api/v1/tenants/",
        {
            "full_name": "Chanda Mwila",
            "phone_number": "0974123381",
            "lease": {
                "unit": str(unit.public_id),
                "start_date": "2027-01-01",
                "end_date": "2026-01-01",
            },
        },
        format="json",
    )
    assert response.status_code == 400
    assert "lease" in response.json()["response_data"]
    assert not Tenant.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload, field",
    [
        ({"full_name": "A", "phone_number": "0971234567"}, "full_name"),
        ({"full_name": "Valid Name", "phone_number": "12345"}, "phone_number"),
        (
            {"full_name": "Valid Name", "phone_number": "0971234567", "email": "not-an-email"},
            "email",
        ),
        ({"phone_number": "0971234567"}, "full_name"),
    ],
)
def test_tenant_validation_errors(manager, payload, field):
    response = manager.post("/api/v1/tenants/", payload, format="json")
    assert response.status_code == 400
    assert field in response.json()["response_data"]
    assert not Tenant.objects.exists()


@pytest.mark.django_db
def test_phone_must_be_unique_within_organization_only(manager, org):
    Tenant.objects.create(organization=org, full_name="First", phone_number="+260971234567")
    duplicate = manager.post(
        "/api/v1/tenants/", {"full_name": "Second", "phone_number": "0971234567"}, format="json"
    )
    assert duplicate.status_code == 400
    assert "phone_number" in duplicate.json()["response_data"]

    other = Organization.objects.create(name="Other Landlord")
    other_client = member_client(other, OrganizationMembership.Role.LANDLORD, "other-owner")
    allowed = other_client.post(
        "/api/v1/tenants/", {"full_name": "Second", "phone_number": "0971234567"}, format="json"
    )
    assert allowed.status_code == 201


@pytest.mark.django_db
def test_tenant_cannot_use_another_organizations_unit(manager):
    other = Organization.objects.create(name="Other Landlord")
    foreign_unit = make_unit(other, property_name="Elsewhere")
    response = manager.post(
        "/api/v1/tenants/",
        {
            "full_name": "Chanda Mwila",
            "phone_number": "0974123381",
            "lease": {
                "unit": str(foreign_unit.public_id),
                "start_date": "2026-11-01",
                "end_date": "2027-10-31",
            },
        },
        format="json",
    )
    assert response.status_code == 400
    assert not Tenant.objects.exists()
    assert not Lease.objects.exists()


@pytest.mark.django_db
def test_tenants_are_scoped_to_the_organization(manager, org):
    Tenant.objects.create(organization=org, full_name="Mine", phone_number="+260971111111")
    other = Organization.objects.create(name="Other Landlord")
    theirs = Tenant.objects.create(
        organization=other, full_name="Theirs", phone_number="+260972222222"
    )

    names = [row["full_name"] for row in manager.get("/api/v1/tenants/").json()["response_data"]]
    assert names == ["Mine"]
    assert manager.get(f"/api/v1/tenants/{theirs.public_id}/").status_code == 404
    assert (
        manager.patch(
            f"/api/v1/tenants/{theirs.public_id}/", {"full_name": "Hijacked"}, format="json"
        ).status_code
        == 404
    )
    theirs.refresh_from_db()
    assert theirs.full_name == "Theirs"


@pytest.mark.django_db
def test_tenant_member_cannot_write_tenants(org):
    member = member_client(org, OrganizationMembership.Role.TENANT, "tenant-member")
    tenant = Tenant.objects.create(
        organization=org, full_name="Existing", phone_number="+260971111111"
    )
    assert member.get("/api/v1/tenants/").status_code == 403
    assert (
        member.post(
            "/api/v1/tenants/", {"full_name": "New", "phone_number": "0972222222"}, format="json"
        ).status_code
        == 403
    )
    assert member.delete(f"/api/v1/tenants/{tenant.public_id}/").status_code == 403
    assert Tenant.objects.count() == 1


@pytest.mark.django_db
def test_tenant_persona_and_anonymous_users_are_blocked(org):
    tenant_user = member_client(org, OrganizationMembership.Role.TENANT, "tenant-user")
    assert tenant_user.get("/api/v1/tenants/").status_code == 403
    assert APIClient().get("/api/v1/tenants/").status_code in {401, 403}
    assert APIClient().post(
        "/api/v1/tenants/", {"full_name": "X Y", "phone_number": "0971234567"}, format="json"
    ).status_code in {401, 403}
    assert not Tenant.objects.exists()


@pytest.mark.django_db
def test_platform_admin_requires_workspace_for_tenants(org):
    Tenant.objects.create(organization=org, full_name="Mine", phone_number="+260971111111")
    admin = User.objects.create_user(username="admin", password="StrongerPass123", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=admin)
    assert client.get("/api/v1/tenants/").status_code == 400
    assert (
        client.post(
            "/api/v1/tenants/",
            {"full_name": "New Person", "phone_number": "0972222222"},
            format="json",
        ).status_code
        == 400
    )


@pytest.mark.django_db
def test_tenant_with_lease_cannot_be_deleted(manager, org):
    unit = make_unit(org)
    tenant = Tenant.objects.create(organization=org, full_name="Kept", phone_number="+260971111111")
    Lease.objects.create(
        organization=org,
        reference="LSE-0001",
        tenant=tenant,
        unit=unit,
        start_date="2026-01-01",
        end_date="2027-01-01",
        monthly_rent="3900.00",
    )
    response = manager.delete(f"/api/v1/tenants/{tenant.public_id}/")
    assert response.status_code == 400
    assert Tenant.objects.filter(pk=tenant.pk).exists()

    loose = Tenant.objects.create(
        organization=org, full_name="Removable", phone_number="+260972222222"
    )
    assert manager.delete(f"/api/v1/tenants/{loose.public_id}/").status_code == 204
