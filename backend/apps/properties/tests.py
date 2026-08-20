import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership

from .models import Property, Unit

User = get_user_model()


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
        role=OrganizationMembership.Role.OWNER,
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
        role=OrganizationMembership.Role.MANAGER,
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

    assert response.status_code == 200
    data = response.json()["response_data"]
    assert data["organization"] is None
    assert data["properties"]["total"] == 0
    assert data["units"]["total"] == 0
    assert data["finance"]["monthly_rent_roll"] == 0
