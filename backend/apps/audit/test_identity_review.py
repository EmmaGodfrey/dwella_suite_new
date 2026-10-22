import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import IdentityVerification

from .models import AuditEvent

pytestmark = pytest.mark.django_db
URL = "/api/v1/platform/identity-verifications/"


@pytest.mark.parametrize("decision", ["approved", "rejected"])
def test_staff_reviews_pending_identity_with_recorded_reason(context, decision):
    client, actor, _, _ = context
    user = get_user_model().objects.create_user(username="applicant")
    verification = IdentityVerification.objects.create(user=user, status="pending")
    path = f"{URL}{verification.pk}/"
    assert client.get(URL).status_code == 200
    assert client.get(path + "document/").status_code == 404
    assert client.post(path + "review/", {"decision": "unknown"}).status_code == 400
    if decision == "rejected":
        assert client.post(path + "review/", {"decision": decision}).status_code == 400
    response = client.post(path + "review/", {
        "decision": decision, "reason": "Document was reviewed",
    }, format="json")
    assert response.status_code == 200, response.content
    verification.refresh_from_db()
    assert verification.status == decision and verification.reviewed_at
    assert AuditEvent.objects.get(action=f"identity.{decision}").actor == actor
    assert client.post(path + "review/", {"decision": decision}).status_code == 400
    client.force_authenticate(user)
    assert client.get(URL).status_code == 403
    assert client.post(path + "review/", {"decision": decision}).status_code == 403
    assert client.get(path + "document/").status_code == 403
