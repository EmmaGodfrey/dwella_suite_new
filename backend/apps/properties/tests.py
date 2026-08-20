import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership

from .models import Property

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
