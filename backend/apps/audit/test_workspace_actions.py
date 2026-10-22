from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError

from apps.organizations.models import Organization, OrganizationMembership

from .models import AuditEvent, SupportSession

pytestmark = pytest.mark.django_db
URL = "/api/v1/platform/workspaces/"


def test_create_workspace_and_edit_profile_are_audited(context):
    client, _, _, _ = context
    owner = get_user_model().objects.create_user(username="workspace-owner")
    assert client.post(URL, {"display_name": "New"}, format="json").status_code == 400
    response = client.post(URL, {
        "display_name": "New workspace", "owner": owner.pk, "currency": "ZMW",
    }, format="json")
    assert response.status_code == 201, response.content
    public_id = response.json()["response_data"]["id"]
    workspace = Organization.objects.get(public_id=public_id)
    assert workspace.memberships.get().user == owner
    path = f"{URL}{public_id}/"
    assert client.patch(path, {"timezone": "Invalid/Zone"}).status_code == 400
    assert client.patch(path, {"currency": "USD"}).status_code == 400
    assert client.patch(path, {"email": "invalid"}).status_code == 400
    assert client.patch(path, {"display_name": "Changed", "is_active": False}).status_code == 200
    workspace.refresh_from_db()
    assert workspace.display_name == "Changed" and workspace.is_active
    assert AuditEvent.objects.filter(action="workspace.created").count() == 1
    assert AuditEvent.objects.filter(action="workspace.updated").count() == 1


def test_suspend_and_reactivate_end_support_sessions_without_revival(context):
    client, _, org, _ = context
    created = client.post("/api/v1/platform/support-sessions/", {
        "organization": str(org.public_id), "reason": "Investigating billing query",
    }, format="json")
    session = SupportSession.objects.get(public_id=created.json()["response_data"]["id"])
    path = f"{URL}{org.public_id}/status/"
    assert client.post(path, {}, format="multipart").status_code == 400
    assert client.post(path, {"active": "bad"}).status_code == 400
    assert client.post(path, {"active": False}, format="json").status_code == 200
    session.refresh_from_db()
    assert session.ended_at
    assert client.post(path, {"active": True}, format="json").status_code == 200
    assert client.get(
        "/api/v1/properties/", HTTP_X_DWELLA_WORKSPACE=str(org.public_id),
    ).status_code == 403
    assert AuditEvent.objects.filter(action="workspace.suspended").exists()


def test_transfer_owner_preserves_an_active_owner_and_demotes_previous_owner(context):
    client, _, org, _ = context
    User = get_user_model()
    old = User.objects.create_user(username="old-owner")
    new = User.objects.create_user(username="new-owner")
    member = OrganizationMembership.objects.create(user=old, organization=org, role="owner")
    path = f"{URL}{org.public_id}/transfer-owner/"
    assert client.post(path, {"owner": "bad"}).status_code == 400
    assert client.post(path, {"owner": new.pk}, format="json").status_code == 200
    member.refresh_from_db()
    assert member.role == "admin"
    assert org.memberships.get(user=new).role == "owner"
    org.is_active = False
    org.save()
    assert client.post(path, {"owner": old.pk}, format="json").status_code == 400


def test_workspace_deletion_requires_superuser_suspension_and_exact_confirmation(context):
    client, actor, org, _ = context
    path = f"{URL}{org.public_id}/"
    body = {"confirmation": f"DELETE {org}"}
    assert client.delete(path, body, format="json").status_code == 403
    actor.is_superuser = True
    actor.save()
    assert client.delete(path, body, format="json").status_code == 400
    org.is_active = False
    org.save()
    assert client.delete(path, {}, format="json").status_code == 400
    with patch.object(Organization, "delete", side_effect=ProtectedError("retained", [])):
        assert client.delete(path, body, format="json").status_code == 400
    assert not AuditEvent.objects.filter(action="workspace.deleted").exists()
    assert client.delete(path, body, format="json").status_code == 204
    assert not Organization.objects.filter(pk=org.pk).exists()
    assert AuditEvent.objects.get(action="workspace.deleted").organization is None


@pytest.mark.parametrize("authenticated", [True, False])
@pytest.mark.parametrize("method, suffix", [("post", ""), ("patch", "{id}/"),
    ("post", "{id}/status/"), ("post", "{id}/transfer-owner/"), ("delete", "{id}/")])
def test_workspace_mutations_deny_non_platform_actors(context, authenticated, method, suffix):
    client, _, org, _ = context
    owner = get_user_model().objects.create_user(username="normal-owner")
    OrganizationMembership.objects.create(user=owner, organization=org, role="owner")
    client.force_authenticate(owner if authenticated else None)
    assert getattr(client, method)(URL + suffix.format(id=org.public_id), {},
                                   format="json").status_code == 403
    assert not AuditEvent.objects.exists()
