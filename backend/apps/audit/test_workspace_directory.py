import pytest
from django.contrib.auth import get_user_model

from apps.properties.models import Property, Unit

pytestmark = pytest.mark.django_db
URL = "/api/v1/platform/workspaces/"


def test_workspace_directory_summaries_filters_and_permissions(context):
    client, _, org, other = context
    prop = Property.objects.create(organization=org, name="Home", address="Plot 1")
    Unit.objects.create(organization=org, property=prop, name="A", rent_amount=1000)
    Unit.objects.create(organization=org, property=prop, name="B", rent_amount=1000)
    response = client.get(URL + f"{org.public_id}/")
    assert response.status_code == 200, response.content
    data = response.json()["response_data"]
    assert data["properties_count"] == 1 and data["units_count"] == 2
    other.is_active = False
    other.save()
    assert len(client.get(URL + "?active=true").json()["response_data"]) == 1
    assert client.get(URL + "?active=bad").status_code == 400
    assert client.get(URL + "?created_after=bad").status_code == 400
    invalid_dates = client.get(URL + "?created_after=2026-10-22&created_before=2025-01-01")
    assert invalid_dates.status_code == 400
    assert client.get(URL + "malformed/").status_code == 404
    client.force_authenticate(get_user_model().objects.create_user(username="non-staff"))
    assert client.get(URL).status_code == 403
    assert client.get(URL + f"{org.public_id}/").status_code == 403
