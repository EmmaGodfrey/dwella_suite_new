from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from .models import AuditEvent, SupportSession
from .support_test_utils import URL, start

pytestmark = pytest.mark.django_db

@pytest.mark.parametrize("reason", ["", "no", " " * 8, "x" * 301, None])
def test_start_validates_reason(context, reason):
    client, _, org, _ = context
    assert (
        client.post(
            URL, {"organization": str(org.public_id), "reason": reason}, format="json"
        ).status_code
        == 400
    )
    assert not SupportSession.objects.exists()
    assert not AuditEvent.objects.exists()



@pytest.mark.parametrize("organization", ["bad", str(uuid4()), None])
def test_start_validates_workspace(context, organization):
    client, _, _, _ = context
    response = client.post(
        URL, {"organization": organization, "reason": "Support review"}, format="json"
    )
    assert response.status_code == 400



def test_suspended_workspace_cannot_be_opened(context):
    client, _, org, _ = context
    org.is_active = False
    org.save()
    assert (
        client.post(
            URL, {"organization": str(org.public_id), "reason": "Support review"}, format="json"
        ).status_code
        == 400
    )



def test_session_lifecycle_and_list_is_private(context):
    client, user, org, other = context
    before = timezone.now()
    session = start(client, org)
    assert before + timedelta(hours=4) <= session.expires_at <= timezone.now() + timedelta(hours=4)
    stranger = get_user_model().objects.create_user(username="stranger-admin", is_staff=True)
    foreign = SupportSession.objects.create(
        admin=stranger,
        organization=other,
        reason="Other call",
        expires_at=timezone.now() + timedelta(hours=4),
    )
    active = client.get(URL + "?active=true").json()["response_data"]
    assert [row["id"] for row in active] == [str(session.public_id)]
    assert client.post(f"{URL}{foreign.public_id}/end/").status_code == 404
    assert client.get(URL + "?active=maybe").status_code == 400
    assert client.post(f"{URL}{session.public_id}/end/").status_code == 200
    client.credentials()
    assert client.post(f"{URL}{session.public_id}/end/").status_code == 200
    assert AuditEvent.objects.filter(action="support_session.ended").count() == 1
    assert client.get(URL + "?active=true").json()["response_data"] == []
    assert len(client.get(URL + "?active=false").json()["response_data"]) == 1
    events = AuditEvent.objects.filter(actor=user)
    assert set(events.values_list("action", flat=True)) == {
        "support_session.started",
        "support_session.ended",
    }



def test_session_start_is_throttled(context):
    client, _, org, _ = context
    for _ in range(10):
        assert (
            client.post(
                URL, {"organization": str(org.public_id), "reason": "Support review"}, format="json"
            ).status_code
            == 201
        )
    assert (
        client.post(
            URL, {"organization": str(org.public_id), "reason": "Support review"}, format="json"
        ).status_code
        == 429
    )
    assert SupportSession.objects.count() == 10



def test_session_authentication_still_enforces_csrf(context):
    _, user, org, _ = context
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)
    response = client.post(
        URL, {"organization": str(org.public_id), "reason": "Support session"}, format="json"
    )
    assert response.status_code == 403
    assert not SupportSession.objects.exists()



def test_malformed_end_id_is_not_a_server_error(context):
    client, _, _, _ = context
    assert client.post(f"{URL}bad-uuid/end/").status_code == 404
