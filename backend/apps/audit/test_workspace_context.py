from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.organizations.models import OrganizationMembership
from apps.properties.models import Property

from .support_test_utils import URL, start

pytestmark = pytest.mark.django_db

@pytest.mark.parametrize(
    "state", ["wrong", "expired", "ended", "different-admin", "malformed", "blank", "unknown"]
)
def test_invalid_context_is_forbidden(context, state):
    client, user, org, other = context
    session = start(client, org)
    if state == "expired":
        session.expires_at = timezone.now() - timedelta(seconds=1)
    elif state == "ended":
        session.ended_at = timezone.now()
    elif state == "different-admin":
        session.admin = get_user_model().objects.create_user(username="other-admin", is_staff=True)
    session.save()
    header = {
        "wrong": str(other.public_id),
        "malformed": "wrong",
        "blank": "",
        "unknown": str(uuid4()),
    }.get(state, str(org.public_id))
    client.credentials(HTTP_X_DWELLA_WORKSPACE=header)
    response = client.get("/api/v1/properties/")
    assert response.status_code == 403
    assert response.json()["success"] is False



def test_non_admin_headers_ignored_and_permissions_unchanged(context):
    client, _, org, other = context
    landlord = get_user_model().objects.create_user(username="landlord")
    OrganizationMembership.objects.create(user=landlord, organization=org, role="owner")
    Property.objects.create(organization=org, name="Owned", address="Plot 1")
    Property.objects.create(organization=other, name="Private", address="Plot 2")
    client.force_authenticate(landlord)
    for header in (str(other.public_id), "malformed"):
        client.credentials(HTTP_X_DWELLA_WORKSPACE=header)
        response = client.get("/api/v1/properties/")
        assert response.status_code == 200
        assert [row["name"] for row in response.json()["response_data"]] == ["Owned"]
    assert client.get(URL).status_code == 403
    assert (
        client.post(
            URL, {"organization": str(org.public_id), "reason": "Try opening"}, format="json"
        ).status_code
        == 403
    )
    client.force_authenticate(None)
    assert client.get(URL).status_code in (401, 403)
    assert client.post(URL, {}, format="json").status_code in (401, 403)



def test_me_reports_context_only_with_header(context):
    client, _, org, _ = context
    assert (
        client.get("/api/v1/accounts/me/").json()["response_data"]["access"]["acting_workspace"]
        is None
    )
    session = start(client, org)
    access = client.get("/api/v1/accounts/me/").json()["response_data"]["access"]
    assert access["acting_workspace"]["session_id"] == str(session.public_id)
    assert access["acting_workspace"]["id"] == str(org.public_id)
    assert all(
        access[key]
        for key in [
            "can_manage_properties",
            "can_manage_organization",
            "can_view_portfolio",
            "can_view_reports",
        ]
    )
    client.credentials()
    assert client.get("/api/v1/properties/").status_code == 400



def test_revoked_staff_access_cannot_reuse_support_session(context):
    client, user, org, _ = context
    start(client, org)
    user.is_staff = False
    user.save(update_fields=["is_staff"])
    assert client.get(URL).status_code == 403
    assert client.get("/api/v1/properties/").status_code == 403
    assert (
        client.get("/api/v1/accounts/me/").json()["response_data"]["access"]["acting_workspace"]
        is None
    )

