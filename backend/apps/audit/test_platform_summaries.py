import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import IdentityVerification

pytestmark = pytest.mark.django_db


def test_workspace_and_identity_summary_totals_and_permissions(context):
    client, _, org, _ = context
    user = get_user_model().objects.create_user(username="summary-applicant")
    IdentityVerification.objects.create(user=user, status="pending")
    org.is_active = False
    org.save()
    workspaces = "/api/v1/platform/workspaces/summary/"
    identities = "/api/v1/platform/identity-verifications/summary/"
    data = client.get(workspaces).json()["response_data"]
    assert data["active"] == 1 and data["suspended"] == 1 and data["new_this_week"] == 2
    assert client.get(identities).json()["response_data"] == {
        "pending": 1, "approved": 0, "rejected": 0,
    }
    base = "/api/v1/platform/identity-verifications/"
    assert client.get(base + "?submitted_after=bad").status_code == 400
    assert client.get(
        base + "?submitted_after=2026-10-22&submitted_before=2025-01-01",
    ).status_code == 400
    for actor in (user, None):
        client.force_authenticate(actor)
        assert client.get(workspaces).status_code == 403
        assert client.get(identities).status_code == 403
