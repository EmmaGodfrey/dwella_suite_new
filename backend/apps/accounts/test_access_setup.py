import re
import time
from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership
from apps.tenants.models import Tenant

from .access_state import email_status, require_new_account_verification
from .models import AccountAccessState, EmailVerificationLink, GuidedTourState, TenantInvitation
from .security import _hotp
from .tours import TOURS

pytestmark = pytest.mark.django_db
VERIFY = "/api/v1/accounts/email-verification/"
CONFIRM = VERIFY + "confirm/"
PREVIEW = "/api/v1/accounts/invitations/preview/"
ACCEPT = "/api/v1/accounts/invitations/accept/"
TOUR = "/api/v1/accounts/guided-tour/"
PASSWORD = "BetterPassphrase27!Dwella"


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture(autouse=True)
def settings_for_access(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def person():
    return get_user_model().objects.create_user(
        username="person@example.com",
        email="person@example.com",
        password=PASSWORD,
        first_name="Chanda",
    )


@pytest.fixture
def workspace(person):
    org = Organization.objects.create(name="Chanda Properties")
    OrganizationMembership.objects.create(user=person, organization=org, role="landlord")
    return org


def email_token():
    return re.search(r"token=([A-Za-z0-9_-]+)", mail.outbox[-1].body)[1]


def test_verification_is_one_use_mailbox_proof_not_a_login(person):
    require_new_account_verification(person)
    client = client_for(person)
    assert client.post(VERIFY).status_code == 200
    token = email_token()
    assert token not in EmailVerificationLink.objects.get().token_hash
    assert APIClient().get(CONFIRM, {"token": token}).status_code == 405
    assert not email_status(person)["verified"]
    assert client.get("/api/v1/organizations/onboarding/").status_code == 403
    assert APIClient().post(CONFIRM, {"token": token}).status_code == 200
    assert email_status(person)["verified"] and not email_status(person)["required"]
    assert not Token.objects.filter(user=person).exists()
    assert client.get("/api/v1/organizations/onboarding/").status_code == 200
    assert APIClient().post(CONFIRM, {"token": token}).status_code == 400


@pytest.mark.parametrize("change", ["expired", "email", "inactive", "revoked"])
def test_verification_rechecks_expiry_account_and_email(person, change):
    client = client_for(person)
    client.post(VERIFY)
    token = email_token()
    link = EmailVerificationLink.objects.get()
    if change == "expired":
        link.expires_at = timezone.now() - timedelta(seconds=1)
        link.save()
    elif change == "revoked":
        link.revoked_at = timezone.now()
        link.save()
    elif change == "email":
        person.email = "new@example.com"
        person.save()
    else:
        person.is_active = False
        person.save()
    assert APIClient().post(CONFIRM, {"token": token}).status_code == 400
    assert not email_status(person)["verified"]


def test_resend_replaces_links_only_after_successful_delivery(person):
    client = client_for(person)
    assert client.post(VERIFY).status_code == 200
    original = email_token()
    assert client.post(VERIFY).status_code == 429
    EmailVerificationLink.objects.update(created_at=timezone.now() - timedelta(minutes=2))
    with patch("apps.accounts.account_mail.send_mail", side_effect=OSError("SMTP down")):
        assert client.post(VERIFY).status_code == 503
    assert EmailVerificationLink.objects.count() == 1
    assert not EmailVerificationLink.objects.get().revoked_at
    assert client.post(VERIFY).status_code == 200
    replacement = email_token()
    assert APIClient().post(CONFIRM, {"token": original}).status_code == 400
    assert APIClient().post(CONFIRM, {"token": replacement}).status_code == 200


def test_legacy_access_is_preserved_without_claiming_verification(person, workspace):
    client = client_for(person)
    assert client.get("/api/v1/properties/").status_code == 200
    status = client.get("/api/v1/accounts/me/").json()["response_data"]["email_verification"]
    assert not status["verified"] and not status["required"]
    assert not AccountAccessState.objects.exists()
    client.post(VERIFY)
    APIClient().post(CONFIRM, {"token": email_token()})
    person.email = "changed@example.com"
    person.save()
    assert client.get("/api/v1/properties/").status_code == 403


def test_mail_failures_remain_generic_and_console_never_logs_secrets(person, settings, capsys):
    with patch("apps.accounts.account_mail.send_mail", side_effect=OSError("SMTP down")):
        good = APIClient().post("/api/v1/accounts/password-reset/", {"email": person.email})
        missing = APIClient().post(
            "/api/v1/accounts/password-reset/", {"email": "absent@example.com"}
        )
    assert good.status_code == missing.status_code == 202
    assert good.json() == missing.json()
    settings.EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    assert client_for(person).post(VERIFY).status_code == 503
    assert "Subject:" not in capsys.readouterr().out
    assert not EmailVerificationLink.objects.exists()


def test_verification_auth_validation_and_throttling(person):
    assert APIClient().post(VERIFY).status_code == 403
    public = APIClient()
    for _ in range(20):
        assert public.post(CONFIRM, {"token": "malformed"}).status_code == 400
    assert public.post(CONFIRM, {"token": "x" * 43}).status_code == 429


def invited_tenant(person, workspace):
    tenant = Tenant.objects.create(
        organization=workspace,
        full_name="Moses Demo",
        phone_number="+260971234567",
        email="moses@example.com",
    )
    response = client_for(person).post(f"/api/v1/tenants/{tenant.public_id}/invite/")
    assert response.status_code == 200, response.content
    return tenant, email_token()


def test_tenant_acceptance_links_only_the_fixed_tenant_and_issues_no_login(person, workspace):
    tenant, token = invited_tenant(person, workspace)
    assert APIClient().get(ACCEPT, {"token": token}).status_code == 405
    preview = APIClient().post(PREVIEW, {"token": token})
    assert preview.status_code == 200 and preview.json()["response_data"]["email"] == tenant.email
    profile = client_for(person).get(f"/api/v1/tenants/{tenant.public_id}/").json()["response_data"]
    assert profile["portal_access"]["status"] == "pending"
    assert "token" not in str(profile["portal_access"])
    result = APIClient().post(
        ACCEPT,
        {
            "token": token,
            "password": PASSWORD,
            "is_staff": True,
            "role": "landlord",
            "email": "attacker@example.com",
        },
    )
    assert result.status_code == 200, result.content
    tenant.refresh_from_db()
    user = tenant.user
    assert user.email == "moses@example.com" and user.check_password(PASSWORD)
    assert (
        not user.is_staff and not user.is_superuser and not Token.objects.filter(user=user).exists()
    )
    assert OrganizationMembership.objects.get(user=user).role == "tenant"
    assert email_status(user)["verified"]
    profile = client_for(person).get(f"/api/v1/tenants/{tenant.public_id}/").json()["response_data"]
    assert profile["portal_access"]["status"] == "linked"
    assert APIClient().post(ACCEPT, {"token": token, "password": PASSWORD}).status_code == 400


@pytest.mark.parametrize("change", ["expired", "email", "suspended", "revoked", "tenant_inactive"])
def test_invitation_rechecks_tenant_workspace_and_link(person, workspace, change):
    tenant, token = invited_tenant(person, workspace)
    if change == "expired":
        TenantInvitation.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    elif change == "email":
        tenant.email = "different@example.com"
        tenant.save()
    elif change == "suspended":
        workspace.is_active = False
        workspace.save()
    elif change == "revoked":
        client_for(person).post(f"/api/v1/tenants/{tenant.public_id}/revoke-invite/")
    else:
        tenant.is_active = False
        tenant.save()
    assert APIClient().post(ACCEPT, {"token": token, "password": PASSWORD}).status_code == 400
    tenant.refresh_from_db()
    assert tenant.user_id is None


def test_inviting_cannot_cross_workspace_and_existing_accounts_must_authenticate(person, workspace):
    tenant, token = invited_tenant(person, workspace)
    existing = get_user_model().objects.create_user(
        username=tenant.email, email=tenant.email, password=PASSWORD
    )
    assert (
        APIClient().post(ACCEPT, {"token": token, "password": "Replacement27!"}).status_code == 403
    )
    assert client_for(person).post(ACCEPT, {"token": token}).status_code == 403
    assert client_for(existing).post(ACCEPT, {"token": token}).status_code == 200
    existing.refresh_from_db()
    assert existing.check_password(PASSWORD)
    assert (
        client_for(existing).post(f"/api/v1/tenants/{tenant.public_id}/invite/").status_code == 403
    )
    org = Organization.objects.create(name="Other organization")
    foreign = Tenant.objects.create(
        organization=org,
        full_name="Foreign",
        phone_number="+260979999999",
        email="foreign@example.com",
    )
    assert (
        client_for(person).post(f"/api/v1/tenants/{foreign.public_id}/invite/").status_code == 404
    )


@pytest.mark.parametrize("kind", ["manager", "staff", "other_workspace", "inactive"])
def test_existing_privileged_or_other_workspace_accounts_cannot_be_claimed(person, workspace, kind):
    tenant, token = invited_tenant(person, workspace)
    target = get_user_model().objects.create_user(
        username=tenant.email,
        email=tenant.email,
        password=PASSWORD,
        is_staff=kind == "staff",
        is_active=kind != "inactive",
    )
    if kind in {"manager", "other_workspace"}:
        org = workspace if kind == "manager" else Organization.objects.create(name="Other")
        OrganizationMembership.objects.create(
            user=target, organization=org, role="landlord" if kind == "manager" else "tenant"
        )
    result = client_for(target).post(ACCEPT, {"token": token})
    assert result.status_code == 403
    tenant.refresh_from_db()
    assert tenant.user_id is None


def test_invitation_password_delivery_and_replacement_failures_are_safe(person, workspace):
    tenant, token = invited_tenant(person, workspace)
    assert APIClient().post(ACCEPT, {"token": token, "password": "short"}).status_code == 400
    with patch("apps.accounts.account_mail.send_mail", side_effect=OSError("Delivery down")):
        assert (
            client_for(person).post(f"/api/v1/tenants/{tenant.public_id}/invite/").status_code
            == 400
        )
    assert not TenantInvitation.objects.get().revoked_at
    assert APIClient().post(PREVIEW, {"token": token}).status_code == 200
    client_for(person).post(f"/api/v1/tenants/{tenant.public_id}/invite/")
    assert APIClient().post(PREVIEW, {"token": token}).status_code == 400


def test_invitation_rejects_email_too_long_for_a_login(person, workspace):
    tenant = Tenant.objects.create(
        organization=workspace, full_name="Moses Demo", phone_number="+260971234567",
        email="a" * 64 + "@" + "b" * 63 + "." + "c" * 30 + ".com",
    )
    assert client_for(person).post(f"/api/v1/tenants/{tenant.public_id}/invite/").status_code == 400
    assert not TenantInvitation.objects.exists()


def test_2fa_cannot_be_overwritten_or_removed_without_current_credentials(person):
    client = client_for(person)
    setup = client.post("/api/v1/accounts/2fa/setup/")
    secret = setup.json()["response_data"]["secret"]
    code = _hotp(secret, int(time.time() // 30))
    assert client.post("/api/v1/accounts/2fa/verify/", {"code": code}).status_code == 200
    assert client.post("/api/v1/accounts/2fa/setup/").status_code == 400
    assert client.post("/api/v1/accounts/2fa/disable/", {}).status_code == 400
    assert (
        client.post(
            "/api/v1/accounts/2fa/disable/", {"password": "wrong", "code": code}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/accounts/2fa/disable/", {"password": PASSWORD, "code": code}
        ).status_code
        == 200
    )


def test_tour_resume_replay_and_added_steps_preserve_progress(person, workspace):
    client = client_for(person)
    assert client.get(TOUR).json()["response_data"]["status"] == "not_started"
    assert not GuidedTourState.objects.exists()
    assert client.patch(TOUR, {"action": "start"}, format="json").status_code == 200
    client.patch(TOUR, {"action": "next", "step": "overview"}, format="json")
    client.patch(TOUR, {"action": "pause"}, format="json")
    resumed = client.patch(TOUR, {"action": "resume"}, format="json").json()["response_data"]
    assert resumed["current_step"] == "properties" and resumed["completed_steps"] == ["overview"]
    for step in ["properties", "tenants", "leases", "billing", "maintenance"]:
        assert (
            client.patch(TOUR, {"action": "next", "step": step}, format="json").status_code == 200
        )
    assert client.get(TOUR).json()["response_data"]["status"] == "completed"
    expanded = deepcopy(TOURS)
    expanded["landlord"]["revision"] = 2
    expanded["landlord"]["steps"].append(
        {
            "id": "new_module",
            "module": "new",
            "title": "New guidance",
            "body": "New step",
            "path": "/profile",
            "target": "profile",
        }
    )
    with patch.dict(TOURS, expanded):
        data = client.get(TOUR).json()["response_data"]
        assert data["updates_available"] and data["pending_steps"] == ["new_module"]
        assert (
            client.patch(TOUR, {"action": "new_steps"}, format="json").json()["response_data"][
                "current_step"
            ]
            == "new_module"
        )
        client.patch(TOUR, {"action": "next"}, format="json")
        assert client.get(TOUR).json()["response_data"]["status"] == "completed"
    replay = client.patch(TOUR, {"action": "replay"}, format="json").json()["response_data"]
    assert replay["current_step"] == "overview" and "properties" in replay["completed_steps"]
    replay_next = client.patch(TOUR, {"action": "next"}, format="json").json()["response_data"]
    assert replay_next["status"] == "in_progress"
    assert replay_next["current_step"] == "properties"


def test_tours_are_own_workspace_scoped_and_do_not_complete_setup(person, workspace):
    client = client_for(person)
    assert APIClient().get(TOUR).status_code == 403
    assert client.patch(TOUR, {"action": "finish"}, format="json").status_code == 400
    client.patch(TOUR, {"action": "start"}, format="json")
    assert (
        client.patch(TOUR, {"action": "next", "step": "not-real"}, format="json").status_code == 400
    )
    client.patch(TOUR, {"action": "skip"}, format="json")
    other = get_user_model().objects.create_user(username="another@example.com")
    OrganizationMembership.objects.create(user=other, organization=workspace, role="landlord")
    assert client_for(other).get(TOUR).json()["response_data"]["status"] == "not_started"
    assert not client.get("/api/v1/organizations/onboarding/").json()["response_data"]["steps"][1][
        "done"
    ]
    assert not any(
        step["path"] == "/reports" for step in client.get(TOUR).json()["response_data"]["steps"]
    )


def test_tour_update_uses_role_after_lock_recheck(person, workspace):
    from .tours import tour_definition

    calls = 0

    def changed_role(user, organization):
        nonlocal calls
        calls += 1
        if calls == 2:
            OrganizationMembership.objects.filter(user=person).update(role="tenant")
        return tour_definition(user, organization)

    with patch("apps.accounts.tours.tour_definition", side_effect=changed_role):
        response = client_for(person).patch(TOUR, {"action": "start"}, format="json")
    assert response.status_code == 200
    assert response.json()["response_data"]["tour_key"] == "tenant_intro"
    assert GuidedTourState.objects.get().tour_key == "tenant_intro"


def test_2fa_removal_rechecks_password_from_locked_account(person):
    from .models import TwoFactorDevice

    device = TwoFactorDevice.objects.create(
        user=person, secret="JBSWY3DPEHPK3PXP", is_confirmed=True
    )
    client = client_for(person)
    fresh = get_user_model().objects.get(pk=person.pk)
    fresh.set_password("Replacement27!Password")
    fresh.save(update_fields=["password"])
    response = client.post(
        "/api/v1/accounts/2fa/disable/",
        {"password": PASSWORD, "code": _hotp(device.secret, int(time.time() // 30))},
    )
    assert response.status_code == 400
    assert TwoFactorDevice.objects.filter(pk=device.pk, is_confirmed=True).exists()


def test_tour_filters_future_paid_steps_and_support_cannot_mutate_progress(person, workspace):
    from apps.subscriptions.models import WorkspaceAccessPolicy

    expanded = deepcopy(TOURS)
    expanded["landlord"]["steps"].append(
        {
            "id": "whatsapp",
            "module": "messages",
            "title": "Messages",
            "body": "Guidance",
            "path": "/profile",
            "target": "messages",
            "feature": "whatsapp_messages",
        }
    )
    WorkspaceAccessPolicy.objects.create(
        organization=workspace, feature_overrides={"whatsapp_messages": {"enabled": False}}
    )
    with patch.dict(TOURS, expanded):
        steps = client_for(person).get(TOUR).json()["response_data"]["steps"]
        assert "whatsapp" not in [step["id"] for step in steps]
    admin = get_user_model().objects.create_user(username="support", is_staff=True)
    client = client_for(admin)
    assert not client.get(TOUR).json()["response_data"]["available"]
    assert client.patch(TOUR, {"action": "start"}, format="json").status_code == 403
    assert not GuidedTourState.objects.exists()


def test_email_gate_also_blocks_assistant_tokens_and_existing_action_jwts(person, workspace):
    from apps.assistant.test_actions import JWT_SETTINGS
    from apps.assistant.test_actions import client_for as assistant_client
    from apps.audit.models import PlatformSettings

    PlatformSettings.objects.create(pk=1, handy_agent_enabled=True)
    with JWT_SETTINGS:
        client = assistant_client(person, workspace)
        require_new_account_verification(person)
        assert client_for(person).post("/api/v1/accounts/handy-agent/token/").status_code == 403
        assert (
            client.post(
                "/api/v1/assistant/properties/",
                {"name": "Blocked", "property_type": "house", "address": "Plot 9"},
                format="json",
            ).status_code
            == 401
        )


def test_pending_verification_is_not_suspension_and_platform_access_is_gated(person, workspace):
    require_new_account_verification(person)
    access = client_for(person).get("/api/v1/accounts/me/").json()["response_data"]["access"]
    assert not access["workspace_suspended"] and not access["can_manage_properties"]
    person.is_superuser = True
    person.save()
    assert client_for(person).get("/api/v1/platform/workspaces/").status_code == 403


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("operation", ["verify_email", "accept_invitation", "reset_password"])
def test_competing_account_link_consumption_is_single_use(person, operation):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.contrib.auth.tokens import default_token_generator
    from django.db import close_old_connections, connection
    from django.utils.encoding import force_bytes
    from django.utils.http import urlsafe_base64_encode

    if connection.vendor != "postgresql":
        pytest.skip("Requires real row locks")
    if operation == "verify_email":
        client_for(person).post(VERIFY)
        path, payload = CONFIRM, {"token": email_token()}
    elif operation == "accept_invitation":
        org = Organization.objects.create(name="Concurrent invitation")
        OrganizationMembership.objects.create(user=person, organization=org, role="landlord")
        _, token = invited_tenant(person, org)
        path, payload = ACCEPT, {"token": token, "password": PASSWORD}
    else:
        path = "/api/v1/accounts/password-reset/confirm/"
        payload = {
            "uid": urlsafe_base64_encode(force_bytes(person.pk)),
            "token": default_token_generator.make_token(person),
            "password": "Replacement27!Password",
        }
    barrier = Barrier(2)

    def consume():
        close_old_connections()
        try:
            client = APIClient()
            barrier.wait(timeout=10)
            return client.post(path, payload, format="json").status_code
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [pool.submit(consume) for _ in range(2)]
        assert sorted(f.result(timeout=20) for f in results) == [200, 400]
