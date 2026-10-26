# ruff: noqa: F811
import pytest
from django.core.cache import cache

from apps.accounts.models import AccountAccessState
from apps.payments.testing import client_for, home  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def reset_cache():
    cache.clear()


def test_removed_tenant_cannot_become_manager_via_setup(home):
    tenant = home["invoice"].tenant
    client = client_for(home["manager"])
    assert (
        client.post(f"/api/v1/tenants/{tenant.public_id}/remove-portal-access/").status_code == 200
    )
    state = AccountAccessState.objects.get(user=home["tenant"])
    assert state.tenant_access_removed
    former = client_for(home["tenant"])
    access = former.get("/api/v1/accounts/me/").json()["response_data"]["access"]
    assert access["tenant_access_removed"] and access["persona"] == "unassigned"
    assert former.get("/api/v1/organizations/onboarding/").status_code == 403
    assert former.post("/api/v1/organizations/onboarding/", {}, format="json").status_code == 403


def test_fresh_invitation_restores_former_tenant_access(home, settings, mailoutbox):
    import re

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.TEST_EMAIL_REDIRECT_TO = ""
    settings.OUTBOUND_EMAIL_ALLOWLIST = []
    tenant = home["invoice"].tenant
    tenant.email = home["tenant"].email
    tenant.save()
    manager = client_for(home["manager"])
    assert (
        manager.post(f"/api/v1/tenants/{tenant.public_id}/remove-portal-access/").status_code == 200
    )
    assert manager.post(f"/api/v1/tenants/{tenant.public_id}/invite/").status_code == 200
    token = re.search(r"token=([A-Za-z0-9_-]+)", mailoutbox[-1].body)[1]
    response = client_for(home["tenant"]).post(
        "/api/v1/accounts/invitations/accept/", {"token": token}, format="json"
    )
    assert response.status_code == 200, response.content
    state = AccountAccessState.objects.get(user=home["tenant"])
    assert not state.tenant_access_removed
    tenant.refresh_from_db()
    assert tenant.user_id == home["tenant"].pk
