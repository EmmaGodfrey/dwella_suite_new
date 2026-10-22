import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from apps.organizations.models import OrganizationMembership

from .models import AuditEvent

pytestmark = pytest.mark.django_db
URL = "/api/v1/platform/users/"


def test_account_deactivation_reactivation_and_self_guards(context):
    client, actor, _, _ = context
    user = get_user_model().objects.create_user(username="target")
    Token.objects.create(user=user)
    assert client.post(f"{URL}{user.pk}/status/", {"active": False}).status_code == 200
    assert not Token.objects.filter(user=user).exists()
    assert client.post(f"{URL}{user.pk}/status/", {"active": True}).status_code == 200
    assert client.post(f"{URL}{actor.pk}/status/", {"active": False}).status_code == 400
    assert client.post(f"{URL}{user.pk}/status/", {}).status_code == 400
    assert AuditEvent.objects.filter(action="user.deactivated").count() == 1


def test_admin_access_and_delete_require_superuser_and_confirmation(context):
    client, actor, _, _ = context
    user = get_user_model().objects.create_user(username="target", first_name="Target")
    path = f"{URL}{user.pk}/"
    assert client.post(path + "admin-access/", {"enabled": True}).status_code == 403
    assert client.delete(path).status_code == 403
    actor.is_superuser = True
    actor.save()
    assert client.post(path + "admin-access/", {"enabled": True}).status_code == 200
    assert client.post(path + "admin-access/", {"enabled": False}).status_code == 200
    assert client.post(f"{URL}{actor.pk}/admin-access/", {"enabled": False}).status_code == 400
    assert client.delete(path, {"confirmation": "DELETE Target"}, format="json").status_code == 400
    assert client.post(path + "status/", {"active": False}).status_code == 200
    assert client.delete(path, {"confirmation": "wrong"}, format="json").status_code == 400
    assert client.delete(path, {"confirmation": "DELETE Target"}, format="json").status_code == 204
    assert AuditEvent.objects.filter(action="user.deleted", resource_id=str(user.pk)).exists()


def test_last_owner_membership_and_deactivation_are_protected(context):
    client, _, org, _ = context
    user = get_user_model().objects.create_user(username="owner")
    OrganizationMembership.objects.create(user=user, organization=org, role="owner")
    path = f"{URL}{user.pk}/"
    data = {"organization": str(org.public_id), "role": "viewer", "remove": True}
    assert client.post(path + "membership/", data, format="json").status_code == 400
    assert client.post(path + "status/", {"active": False}).status_code == 400
    assert client.post(path + "membership/", {**data, "role": "invalid"}).status_code == 400
