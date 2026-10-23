from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership

from .models import Property, Unit

User = get_user_model()


@pytest.fixture
def property_client(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user = User.objects.create_user(username="photo-manager", password="StrongerPass123")
    organization = Organization.objects.create(name="Photo Portfolio")
    OrganizationMembership.objects.create(
        organization=organization, user=user, role=OrganizationMembership.Role.LANDLORD
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client, organization


def cover_upload(image_format="JPEG"):
    buffer = BytesIO()
    Image.new("RGB", (64, 48), "green").save(buffer, format=image_format)
    return SimpleUploadedFile(
        f"cover.{image_format.lower()}", buffer.getvalue(),
        content_type=f"image/{image_format.lower()}",
    )


@pytest.mark.django_db
def test_property_cover_create_edit_list_and_dashboard(property_client):
    client, organization = property_client
    response = client.post("/api/v1/properties/", {
        "name": "Photo Property", "address": "Plot 10", "property_type": "house",
        "cover_image": cover_upload(),
    }, format="multipart")
    assert response.status_code == 201
    data = response.json()["response_data"]
    assert "/media/properties/covers/" in data["cover_image"]
    property_obj = Property.objects.get(public_id=data["id"])
    assert property_obj.organization == organization
    assert property_obj.cover_image.storage.exists(property_obj.cover_image.name)
    Unit.objects.create(
        organization=organization, property=property_obj, name="A1",
        rent_amount="6000", occupancy_status="occupied",
    )
    Unit.objects.create(
        organization=organization, property=property_obj, name="A2",
        rent_amount="5000", occupancy_status="maintenance",
    )
    listed = client.get("/api/v1/properties/").json()["response_data"][0]
    assert listed["cover_image"] == data["cover_image"]
    assert listed["units_count"] == 2
    assert listed["occupied_units"] == 1
    assert listed["maintenance_units"] == 1
    assert listed["vacant_units"] == 0
    assert listed["reserved_units"] == 0
    assert listed["monthly_rent"] == "11000.00"
    assert listed["occupied_rent"] == "6000.00"
    unit_list = client.get(f"/api/v1/properties/units/?property={data['id']}")
    assert unit_list.status_code == 200
    assert [unit["name"] for unit in unit_list.json()["response_data"]] == ["A1", "A2"]
    invalid_filter = client.get("/api/v1/properties/units/?property=not-a-uuid")
    assert invalid_filter.status_code == 400
    dashboard = client.get("/api/v1/properties/dashboard/").json()["response_data"]
    recent = dashboard["recent_properties"]
    assert recent[0]["cover_image"] == data["cover_image"]

    url = f"/api/v1/properties/{data['id']}/"
    updated = client.patch(url, {"cover_image": cover_upload("PNG")}, format="multipart")
    assert updated.status_code == 200
    assert updated.json()["response_data"]["cover_image"] != data["cover_image"]
    removed = client.patch(url, {"cover_image": ""}, format="multipart")
    assert removed.status_code == 200
    assert removed.json()["response_data"]["cover_image"] is None


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["invalid", "oversized", "unsupported"])
def test_property_rejects_invalid_covers(property_client, kind):
    client, _ = property_client
    photo = cover_upload("GIF" if kind == "unsupported" else "JPEG")
    if kind == "invalid":
        photo = SimpleUploadedFile("fake.jpg", b"not an image", content_type="image/jpeg")
    elif kind == "oversized":
        photo = SimpleUploadedFile("large.jpg", photo.read() + b"0" * (5 * 1024 * 1024))
    response = client.post("/api/v1/properties/", {
        "name": "Invalid photo", "address": "Plot 10", "property_type": "house",
        "cover_image": photo,
    }, format="multipart")
    assert response.status_code == 400
    assert response.json()["success"] is False
    assert not Property.objects.exists()


@pytest.mark.django_db
def test_property_photo_is_optional_and_required_fields_are_validated(property_client):
    client, _ = property_client
    invalid = client.post("/api/v1/properties/", {"name": "", "address": ""}, format="json")
    assert invalid.status_code == 400
    valid = client.post("/api/v1/properties/", {
        "name": "Without photo", "address": "Plot 10", "property_type": "house",
    }, format="json")
    assert valid.status_code == 201
    assert valid.json()["response_data"]["cover_image"] is None


@pytest.mark.django_db
def test_property_cover_cannot_be_changed_by_another_organization(property_client):
    client, _ = property_client
    other = Organization.objects.create(name="Other portfolio")
    property_obj = Property.objects.create(
        organization=other, name="Private property", address="Plot 12", property_type="house",
    )
    response = client.patch(
        f"/api/v1/properties/{property_obj.public_id}/",
        {"cover_image": cover_upload()}, format="multipart",
    )
    assert response.status_code == 404
    assert client.get("/api/v1/properties/").json()["response_data"] == []
    property_obj.refresh_from_db()
    assert not property_obj.cover_image


@pytest.mark.django_db
def test_unit_filter_does_not_expose_another_organizations_units(property_client):
    client, _ = property_client
    other = Organization.objects.create(name="Unit owner")
    private_property = Property.objects.create(
        organization=other, name="Private building", address="Plot 14", property_type="house",
    )
    Unit.objects.create(
        organization=other, property=private_property, name="Private unit", rent_amount="1000",
    )
    response = client.get(f"/api/v1/properties/units/?property={private_property.public_id}")
    assert response.status_code == 200
    assert response.json()["response_data"] == []


@pytest.mark.django_db
def test_unit_can_be_created_and_edited_with_property_public_id(property_client):
    client, organization = property_client
    property_obj = Property.objects.create(
        organization=organization, name="Unit building", address="Plot 20",
        property_type="apartment",
    )
    created = client.post("/api/v1/properties/units/", {
        "property": str(property_obj.public_id), "name": "A1", "rent_amount": "6500.00",
        "occupancy_status": "vacant", "bedrooms": 2, "bathrooms": "1.5",
    }, format="json")
    assert created.status_code == 201
    data = created.json()["response_data"]
    assert data["property"] == str(property_obj.public_id)
    unit = Unit.objects.get(public_id=data["id"])
    assert unit.organization == organization

    updated = client.patch(f"/api/v1/properties/units/{data['id']}/", {
        "name": "A2", "occupancy_status": "occupied", "rent_amount": "7000.00",
    }, format="json")
    assert updated.status_code == 200
    assert updated.json()["response_data"]["name"] == "A2"
    assert updated.json()["response_data"]["occupancy_status"] == "occupied"


@pytest.mark.django_db
def test_unit_cannot_be_attached_to_another_organizations_property(property_client):
    client, organization = property_client
    own_property = Property.objects.create(
        organization=organization, name="Own building", address="Plot 21",
        property_type="apartment",
    )
    other = Organization.objects.create(name="Other unit portfolio")
    private_property = Property.objects.create(
        organization=other, name="Private building", address="Plot 22", property_type="apartment",
    )
    created = client.post("/api/v1/properties/units/", {
        "property": str(private_property.public_id), "name": "Private A1", "rent_amount": "6500.00",
    }, format="json")
    assert created.status_code == 400
    assert created.json()["success"] is False
    assert not Unit.objects.exists()

    own_unit = Unit.objects.create(
        organization=organization, property=own_property, name="A1", rent_amount="6500.00",
    )
    changed = client.patch(f"/api/v1/properties/units/{own_unit.public_id}/", {
        "property": str(private_property.public_id),
    }, format="json")
    assert changed.status_code == 400
    own_unit.refresh_from_db()
    assert own_unit.property == own_property

    hidden = client.patch(f"/api/v1/properties/units/{own_unit.public_id}/", {
        "property": "not-a-uuid",
    }, format="json")
    assert hidden.status_code == 400

    private_unit = Unit.objects.create(
        organization=other, property=private_property, name="Private A1", rent_amount="5000.00",
    )
    denied = client.patch(f"/api/v1/properties/units/{private_unit.public_id}/", {
        "name": "Changed",
    }, format="json")
    assert denied.status_code == 404
    private_unit.refresh_from_db()
    assert private_unit.name == "Private A1"


@pytest.mark.django_db
def test_unit_creation_requires_authentication():
    response = APIClient().post("/api/v1/properties/units/", {
        "name": "A1", "rent_amount": "5000.00",
    }, format="json")
    assert response.status_code in {401, 403}
    assert not Unit.objects.exists()


@pytest.mark.django_db
def test_property_upload_requires_authentication():
    response = APIClient().post("/api/v1/properties/", {
        "name": "Unauthenticated", "cover_image": cover_upload(),
    }, format="multipart")
    assert response.status_code in {401, 403}
    assert not Property.objects.exists()


@pytest.mark.django_db
def test_property_list_uses_standard_paginated_envelope():
    user = User.objects.create_user(
        username="owner@example.com",
        email="owner@example.com",
        password="StrongerPass123",
    )
    organization = Organization.objects.create(name="Dwella Test", display_name="Dwella Test")
    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationMembership.Role.LANDLORD,
    )
    Property.objects.create(
        organization=organization,
        name="Rhodes Park Flats",
        property_type=Property.PropertyType.APARTMENT,
        address="Rhodes Park",
        town="Lusaka",
        province="Lusaka",
    )

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get("/api/v1/properties/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["response_code"] == 200
    assert payload["response_message"] == "Operation completed successfully"
    assert payload["pagination"]["count"] == 1
    assert payload["pagination"]["page"] == 1
    assert payload["response_data"][0]["name"] == "Rhodes Park Flats"


@pytest.mark.django_db
def test_dashboard_summary_returns_organization_metrics():
    user = User.objects.create_user(
        username="manager@example.com",
        email="manager@example.com",
        password="StrongerPass123",
    )
    organization = Organization.objects.create(name="Dwella Metrics", display_name="Metrics")
    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationMembership.Role.LANDLORD,
    )
    property_one = Property.objects.create(
        organization=organization,
        name="Kabulonga Heights",
        property_type=Property.PropertyType.APARTMENT,
        management_status=Property.ManagementStatus.MANAGED,
        address="Kabulonga Road",
        town="Lusaka",
        province="Lusaka",
    )
    property_two = Property.objects.create(
        organization=organization,
        name="Makeni Retail Park",
        property_type=Property.PropertyType.COMMERCIAL,
        management_status=Property.ManagementStatus.PROSPECT,
        address="Makeni",
        town="Lusaka",
        province="Lusaka",
    )
    Unit.objects.create(
        organization=organization,
        property=property_one,
        name="A1",
        rent_amount="6500.00",
        occupancy_status=Unit.OccupancyStatus.OCCUPIED,
    )
    Unit.objects.create(
        organization=organization,
        property=property_one,
        name="A2",
        rent_amount="6500.00",
        occupancy_status=Unit.OccupancyStatus.VACANT,
    )
    Unit.objects.create(
        organization=organization,
        property=property_two,
        name="Shop 01",
        rent_amount="12000.00",
        occupancy_status=Unit.OccupancyStatus.OCCUPIED,
    )

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get("/api/v1/properties/dashboard/")

    assert response.status_code == 200
    payload = response.json()
    data = payload["response_data"]
    assert payload["success"] is True
    assert data["organization"]["display_name"] == "Metrics"
    assert data["properties"]["total"] == 2
    assert data["properties"]["managed"] == 1
    assert data["properties"]["prospect"] == 1
    assert data["units"]["total"] == 3
    assert data["units"]["occupied"] == 2
    assert data["units"]["vacant"] == 1
    assert data["units"]["occupancy_rate"] == 66.7
    assert data["finance"]["monthly_rent_roll"] == 25000.0
    assert data["finance"]["occupied_rent_roll"] == 18500.0
    assert data["finance"]["vacancy_loss"] == 6500.0
    assert data["portfolio"]["average_units_per_property"] == 1.5
    assert len(data["recent_properties"]) == 2
    occupied = {item["name"]: item["occupied_units"] for item in data["recent_properties"]}
    assert occupied == {"Kabulonga Heights": 1, "Makeni Retail Park": 1}
    assert data["portfolio"]["towns"] == ["Lusaka"]
    assert data["portfolio"]["towns_count"] == 1
    assert data["top_units"][0]["name"] == "Shop 01"


@pytest.mark.django_db
def test_dashboard_summary_requires_authentication():
    client = APIClient()
    response = client.get("/api/v1/properties/dashboard/")

    assert response.status_code in {401, 403}
    payload = response.json()
    assert payload["success"] is False


@pytest.mark.django_db
def test_dashboard_summary_handles_user_without_organization():
    user = User.objects.create_user(
        username="solo@example.com",
        email="solo@example.com",
        password="StrongerPass123",
    )
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get("/api/v1/properties/dashboard/")

    assert response.status_code == 403
    assert response.json()["success"] is False


@pytest.mark.django_db
@pytest.mark.parametrize("staff,superuser", [(True, False), (False, True)])
def test_platform_admin_dashboard_summary_does_not_grant_portfolio_access(staff, superuser):
    admin = User.objects.create_user(
        username="platform@example.com",
        email="platform@example.com",
        password="StrongerPass123",
        is_staff=staff,
        is_superuser=superuser,
    )
    first = Organization.objects.create(name="First Landlord")
    second = Organization.objects.create(name="Second Landlord")
    for index, organization in enumerate((first, second), start=1):
        owner = User.objects.create_user(
            username=f"owner{index}@example.com",
            email=f"owner{index}@example.com",
            password="StrongerPass123",
        )
        OrganizationMembership.objects.create(
            organization=organization,
            user=owner,
            role=OrganizationMembership.Role.LANDLORD,
        )
        Property.objects.create(
            organization=organization,
            name=f"Portfolio {index}",
            property_type=Property.PropertyType.APARTMENT,
            address=f"Plot {index}",
        )

    client = APIClient()
    client.force_authenticate(user=admin)
    dashboard = client.get("/api/v1/properties/dashboard/")
    create = client.post(
        "/api/v1/properties/",
        {"name": "Admin Property", "property_type": "house", "address": "HQ"},
        format="json",
    )

    assert dashboard.status_code == 200
    summary = dashboard.json()["response_data"]
    assert summary["platform"] == {"organizations": 2, "landlords": 2}
    assert summary["properties"]["total"] == 2
    assert summary["recent_properties"] == []
    assert summary["top_units"] == []
    assert summary["portfolio"]["towns"] == []
    assert summary["access"]["can_view_portfolio"] is False
    assert client.get("/api/v1/properties/").status_code == 400
    assert create.status_code == 400
    assert not Property.objects.filter(name="Admin Property").exists()


@pytest.mark.django_db
def test_tenant_member_cannot_read_or_change_portfolio():
    user = User.objects.create_user(
        username="tenant-member@example.com",
        email="tenant-member@example.com",
        password="StrongerPass123",
    )
    organization = Organization.objects.create(name="Read Only Portfolio")
    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationMembership.Role.TENANT,
    )
    Property.objects.create(
        organization=organization,
        name="Visible Property",
        property_type=Property.PropertyType.HOUSE,
        address="Plot 1",
    )
    client = APIClient()
    client.force_authenticate(user=user)

    listed = client.get("/api/v1/properties/")
    created = client.post(
        "/api/v1/properties/",
        {"name": "Forbidden", "property_type": "house", "address": "Plot 2"},
        format="json",
    )

    assert listed.status_code == 403
    assert created.status_code == 403
    assert Property.objects.count() == 1


@pytest.mark.django_db
def test_tenant_cannot_access_landlord_portfolio_endpoints():
    tenant = User.objects.create_user(
        username="tenant@example.com",
        email="tenant@example.com",
        password="StrongerPass123",
    )
    organization = Organization.objects.create(name="Tenant Home")
    OrganizationMembership.objects.create(
        organization=organization,
        user=tenant,
        role=OrganizationMembership.Role.TENANT,
    )
    client = APIClient()
    client.force_authenticate(user=tenant)

    assert client.get("/api/v1/properties/").status_code == 403
    assert client.get("/api/v1/properties/dashboard/").status_code == 403
