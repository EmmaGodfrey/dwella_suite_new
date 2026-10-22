import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings

from apps.organizations.models import OrganizationMembership

from .models import AuditEvent

pytestmark = pytest.mark.django_db
URL = "/api/v1/platform/users/"


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@pytest.mark.parametrize("kind", ["landlord", "member", "platform_admin"])
def test_create_user_sends_set_password_and_provisions_requested_account(context, kind):
    client, actor, org, _ = context
    actor.is_superuser = True
    actor.save()
    response = client.post(URL, {
        "full_name": "New Landlord", "email": "new@example.com", "account_type": kind,
        "workspace_name": "New Portfolio", "organization": str(org.public_id), "role": "manager",
    }, format="json")
    assert response.status_code == 201, response.content
    user = get_user_model().objects.get(email="new@example.com")
    assert not user.has_usable_password()
    assert user.is_staff is (kind == "platform_admin")
    assert len(mail.outbox) == 1 and "reset_token=" in mail.outbox[0].body
    if kind != "platform_admin":
        membership = user.organization_memberships.get()
        assert membership.role == ("owner" if kind == "landlord" else "manager")
    assert AuditEvent.objects.get(action="user.created").actor == actor


def test_staff_cannot_create_admin_and_invalid_creation_is_atomic(context):
    client, _, _, _ = context
    response = client.post(URL, {
        "full_name": "New Admin", "email": "new@example.com", "account_type": "platform_admin",
    }, format="json")
    assert response.status_code == 403
    assert not get_user_model().objects.filter(email="new@example.com").exists()
    assert client.post(URL, [], format="json").status_code == 400


def test_users_search_filters_and_profile_update_are_staff_only(context):
    client, _, org, _ = context
    target = get_user_model().objects.create_user(username="owner", email="owner@example.com")
    OrganizationMembership.objects.create(organization=org, user=target, role="owner")
    listed = client.get(URL + f"?search=owner&workspace={org.public_id}&role=owner&active=true")
    assert [u["id"] for u in listed.json()["response_data"]] == [target.pk]
    assert client.get(URL + "?workspace=bad").status_code == 400
    assert client.get(URL + "?two_factor=invalid").status_code == 400
    edited = client.patch(URL + f"{target.pk}/", {
        "full_name": "Updated Owner", "phone_number": "+260971234567",
    }, format="json")
    assert edited.status_code == 200
    assert edited.json()["response_data"]["first_name"] == "Updated"
    client.force_authenticate(target)
    assert client.get(URL).status_code == 403
    assert client.get(URL + f"{target.pk}/").status_code == 403
    assert client.patch(URL + f"{target.pk}/", {}, format="json").status_code == 403
    assert client.post(URL, {}, format="json").status_code == 403
    client.force_authenticate(None)
    assert client.get(URL).status_code == 403
