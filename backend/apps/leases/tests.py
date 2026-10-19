import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership
from apps.properties.models import Property, Unit
from apps.tenants.models import Tenant

from .models import Lease

User = get_user_model()


def member_client(organization, role, username):
    user = User.objects.create_user(username=username, password="StrongerPass123")
    OrganizationMembership.objects.create(organization=organization, user=user, role=role)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def org():
    return Organization.objects.create(name="Kafue Ridge Properties")


@pytest.fixture
def manager(org):
    return member_client(org, OrganizationMembership.Role.MANAGER, "manager")


@pytest.fixture
def unit(org):
    property_obj = Property.objects.create(
        organization=org, name="Mutendere Court", property_type="apartment", address="Plot 4471"
    )
    return Unit.objects.create(
        organization=org, property=property_obj, name="2A", rent_amount="3900.00"
    )


@pytest.fixture
def tenant(org):
    return Tenant.objects.create(
        organization=org, full_name="Chanda Mwila", phone_number="+260974123381"
    )


def lease_payload(tenant, unit, **overrides):
    payload = {
        "tenant": str(tenant.public_id),
        "unit": str(unit.public_id),
        "start_date": "2026-11-01",
        "end_date": "2027-10-31",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_create_draft_lease_with_unit_rent_and_sequential_references(manager, tenant, unit, org):
    first = manager.post("/api/v1/leases/", lease_payload(tenant, unit), format="json")
    assert first.status_code == 201
    data = first.json()["response_data"]
    assert data["reference"] == "LSE-0001"
    assert data["status"] == "draft"
    assert data["monthly_rent"] == "3900.00"
    assert data["property_name"] == "Mutendere Court"
    unit.refresh_from_db()
    assert unit.occupancy_status == "vacant"  # a draft does not occupy the unit yet

    other_unit = Unit.objects.create(
        organization=org, property=unit.property, name="2B", rent_amount="4100.00"
    )
    second = manager.post(
        "/api/v1/leases/", lease_payload(tenant, other_unit, monthly_rent="4000.00"), format="json"
    )
    assert second.json()["response_data"]["reference"] == "LSE-0002"
    assert second.json()["response_data"]["monthly_rent"] == "4000.00"


@pytest.mark.django_db
def test_activate_and_end_lease_update_unit_and_tenant(manager, tenant, unit):
    lease_id = manager.post("/api/v1/leases/", lease_payload(tenant, unit), format="json").json()[
        "response_data"
    ]["id"]

    activated = manager.post(f"/api/v1/leases/{lease_id}/activate/")
    assert activated.status_code == 200
    assert activated.json()["response_data"]["status"] == "active"
    unit.refresh_from_db()
    tenant.refresh_from_db()
    assert unit.occupancy_status == "occupied"
    assert tenant.status == "active"

    assert manager.post(f"/api/v1/leases/{lease_id}/activate/").status_code == 400

    ended = manager.post(f"/api/v1/leases/{lease_id}/end/")
    assert ended.status_code == 200
    assert ended.json()["response_data"]["status"] == "ended"
    unit.refresh_from_db()
    tenant.refresh_from_db()
    assert unit.occupancy_status == "vacant"
    assert tenant.status == "past"
    assert manager.post(f"/api/v1/leases/{lease_id}/end/").status_code == 400


@pytest.mark.django_db
def test_unit_can_hold_only_one_open_lease(manager, tenant, unit, org):
    assert (
        manager.post("/api/v1/leases/", lease_payload(tenant, unit), format="json").status_code
        == 201
    )
    someone_else = Tenant.objects.create(
        organization=org, full_name="Second", phone_number="+260975550000"
    )
    clash = manager.post("/api/v1/leases/", lease_payload(someone_else, unit), format="json")
    assert clash.status_code == 400
    assert "unit" in clash.json()["response_data"]
    assert Lease.objects.count() == 1


@pytest.mark.django_db
def test_ended_lease_frees_the_unit_for_a_new_one(manager, tenant, unit):
    lease_id = manager.post(
        "/api/v1/leases/", lease_payload(tenant, unit, activate=True), format="json"
    ).json()["response_data"]["id"]
    manager.post(f"/api/v1/leases/{lease_id}/end/")
    again = manager.post(
        "/api/v1/leases/",
        lease_payload(tenant, unit, start_date="2027-11-01", end_date="2028-10-31"),
        format="json",
    )
    assert again.status_code == 201


@pytest.mark.django_db
@pytest.mark.parametrize(
    "overrides, field",
    [
        ({"end_date": "2026-10-01"}, "end_date"),
        ({"end_date": "2026-11-01"}, "end_date"),
        ({"monthly_rent": "0"}, "monthly_rent"),
        ({"rent_due_day": 31}, "rent_due_day"),
        ({"rent_due_day": 0}, "rent_due_day"),
        ({"late_fee_percent": "150"}, "late_fee_percent"),
        ({"deposit_amount": "-1"}, "deposit_amount"),
        ({"notice_period_months": 24}, "notice_period_months"),
        ({"start_date": "not-a-date"}, "start_date"),
    ],
)
def test_lease_validation_errors(manager, tenant, unit, overrides, field):
    response = manager.post(
        "/api/v1/leases/", lease_payload(tenant, unit, **overrides), format="json"
    )
    assert response.status_code == 400
    assert field in response.json()["response_data"]
    assert not Lease.objects.exists()


@pytest.mark.django_db
def test_lease_cannot_reference_another_organizations_tenant_or_unit(manager, tenant, unit):
    other = Organization.objects.create(name="Other Landlord")
    foreign_tenant = Tenant.objects.create(
        organization=other, full_name="Foreign", phone_number="+260979999999"
    )
    foreign_property = Property.objects.create(
        organization=other, name="Elsewhere", property_type="house", address="X"
    )
    foreign_unit = Unit.objects.create(
        organization=other, property=foreign_property, name="Z", rent_amount="100"
    )

    assert (
        manager.post(
            "/api/v1/leases/", lease_payload(foreign_tenant, unit), format="json"
        ).status_code
        == 400
    )
    assert (
        manager.post(
            "/api/v1/leases/", lease_payload(tenant, foreign_unit), format="json"
        ).status_code
        == 400
    )
    assert not Lease.objects.exists()


@pytest.mark.django_db
def test_active_lease_terms_are_locked_but_draft_can_be_edited(manager, tenant, unit):
    lease_id = manager.post("/api/v1/leases/", lease_payload(tenant, unit), format="json").json()[
        "response_data"
    ]["id"]
    assert (
        manager.patch(
            f"/api/v1/leases/{lease_id}/", {"monthly_rent": "4200.00"}, format="json"
        ).status_code
        == 200
    )

    manager.post(f"/api/v1/leases/{lease_id}/activate/")
    locked = manager.patch(
        f"/api/v1/leases/{lease_id}/", {"monthly_rent": "5000.00"}, format="json"
    )
    assert locked.status_code == 400
    assert (
        manager.patch(
            f"/api/v1/leases/{lease_id}/", {"notes": "Pays by Airtel"}, format="json"
        ).status_code
        == 200
    )
    assert (
        manager.patch(f"/api/v1/leases/{lease_id}/", {"status": "ended"}, format="json").json()[
            "response_data"
        ]["status"]
        == "active"
    )


@pytest.mark.django_db
def test_only_draft_leases_can_be_deleted(manager, tenant, unit):
    lease_id = manager.post(
        "/api/v1/leases/", lease_payload(tenant, unit, activate=True), format="json"
    ).json()["response_data"]["id"]
    assert manager.delete(f"/api/v1/leases/{lease_id}/").status_code == 400
    assert Lease.objects.count() == 1


@pytest.mark.django_db
def test_viewer_cannot_create_or_change_lease_state(org, tenant, unit, manager):
    lease_id = manager.post("/api/v1/leases/", lease_payload(tenant, unit), format="json").json()[
        "response_data"
    ]["id"]
    viewer = member_client(org, OrganizationMembership.Role.VIEWER, "viewer")
    assert viewer.get(f"/api/v1/leases/{lease_id}/").status_code == 200
    assert (
        viewer.post("/api/v1/leases/", lease_payload(tenant, unit), format="json").status_code
        == 403
    )
    assert viewer.post(f"/api/v1/leases/{lease_id}/activate/").status_code == 403
    assert Lease.objects.get(public_id=lease_id).status == "draft"


@pytest.mark.django_db
def test_other_organization_cannot_see_or_end_lease(tenant, unit, manager):
    lease_id = manager.post(
        "/api/v1/leases/", lease_payload(tenant, unit, activate=True), format="json"
    ).json()["response_data"]["id"]
    other = Organization.objects.create(name="Other Landlord")
    outsider = member_client(other, OrganizationMembership.Role.OWNER, "outsider")
    assert outsider.get(f"/api/v1/leases/{lease_id}/").status_code == 404
    assert outsider.post(f"/api/v1/leases/{lease_id}/end/").status_code == 404
    assert Lease.objects.get(public_id=lease_id).status == "active"


@pytest.mark.django_db
def test_tenant_persona_and_anonymous_cannot_use_leases(org, tenant, unit):
    tenant_user = member_client(org, OrganizationMembership.Role.TENANT, "tenant-user")
    assert tenant_user.get("/api/v1/leases/").status_code == 403
    assert APIClient().post(
        "/api/v1/leases/", lease_payload(tenant, unit), format="json"
    ).status_code in {401, 403}
    assert not Lease.objects.exists()


@pytest.mark.django_db
def test_lease_filters_by_property_and_status(manager, tenant, unit):
    manager.post("/api/v1/leases/", lease_payload(tenant, unit), format="json")
    by_property = manager.get(f"/api/v1/leases/?property={unit.property.public_id}").json()[
        "response_data"
    ]
    assert len(by_property) == 1
    assert manager.get("/api/v1/leases/?status=active").json()["response_data"] == []
