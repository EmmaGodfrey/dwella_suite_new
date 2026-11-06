"""Website-only WhatsApp verification: ownership, delivery, consent and abuse limits."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.access_state import mark_email_verified
from apps.common.provider_http import ProviderRejected

from . import test_whatsapp as base
from .models import NotificationPhoneLink, NotificationPreferences, PhoneMessagingConsent
from .phone_links import receive_link
from .whatsapp.models import WhatsAppBinding

pytestmark = pytest.mark.django_db(transaction=True)
config = base.config
house = base.house
URL = base.BASE + "phone-verification/"


@pytest.fixture(autouse=True)
def approved(settings, config):
    settings.WHATSAPP_OTP_ENABLED = True
    settings.WHATSAPP_OTP_TEMPLATE = "dwella_verify_number"
    settings.WHATSAPP_OTP_LANGUAGE = "en"
    settings.APPROVED_WHATSAPP_TEMPLATES = ["dwella_verify_number:en"]


def issue(house, consent=False):
    sent = []

    def send(url, payload, auth):
        sent.append((payload, connection.in_atomic_block))
        return {"messages": [{"id": "wamid.synthetic-code"}]}

    with (
        patch("apps.notifications.phone_codes.secrets.randbelow", return_value=24680),
        patch(
            "apps.notifications.phone_codes.post_json",
            side_effect=send,
        ) as post,
    ):
        response = base.client(house["tenant"]).post(
            URL,
            {
                "phone": base.PHONE,
                "consent": consent,
            },
            format="json",
        )
    assert response.status_code == 202, response.content
    assert post.call_count == 1
    payload, locked = sent[0]
    assert not locked
    assert payload["to"] == base.PHONE[1:]
    assert payload["type"] == "template"
    assert payload["template"]["name"] == "dwella_verify_number"
    assert payload["template"]["components"][0]["parameters"][0]["text"] == "024680"
    assert payload["template"]["components"][1]["parameters"][0]["text"] == "024680"
    assert "024680" not in response.content.decode()
    return response.json()["response_data"]


def confirm(house, identity, code="024680", user=None):
    return base.client(user or house["tenant"]).post(
        URL,
        {
            "complete": identity,
            "code": code,
        },
        format="json",
    )


@pytest.mark.parametrize("consent", [False, True])
def test_code_sent_then_entered_on_website_connects_without_inbound(house, consent):
    challenge = issue(house, consent)
    link = NotificationPhoneLink.objects.get()
    assert link.verification_nonce and link.auth_stamp and link.delivery_status == "sent"
    assert "024680" not in link.token_hash
    assert not WhatsAppBinding.objects.exists() and not PhoneMessagingConsent.objects.exists()
    response = confirm(house, challenge["id"])
    assert response.status_code == 200, response.content
    assert WhatsAppBinding.objects.get().user_id == house["tenant"].pk
    contact = PhoneMessagingConsent.objects.get()
    assert contact.allowed is consent and contact.last_inbound_at is None
    assert NotificationPreferences.objects.get().whatsapp_enabled is consent
    assert confirm(house, challenge["id"]).status_code == 400


def test_inbound_connect_and_legacy_completion_cannot_bypass_code(house):
    challenge = issue(house)
    assert not receive_link("whatsapp", base.PHONE, "CONNECT 024680", timezone.now())
    api = base.client(house["tenant"])
    result = api.post(
        base.BASE + "phone-link/",
        {
            "channel": "whatsapp",
            "complete": challenge["id"],
        },
        format="json",
    )
    assert result.status_code == 400
    assert not WhatsAppBinding.objects.exists()


def test_bad_codes_persist_attempts_and_lock_out_correct_code(house):
    challenge = issue(house)
    for _ in range(5):
        assert confirm(house, challenge["id"], "999999").status_code == 400
    assert NotificationPhoneLink.objects.get().failed_attempts == 5
    assert confirm(house, challenge["id"]).status_code == 400
    assert not WhatsAppBinding.objects.exists()


@pytest.mark.parametrize(
    "change", ["expiry", "password", "email", "unverified", "suspended", "role", "stop"]
)
def test_changed_identity_or_expired_code_cannot_connect(house, change):
    from apps.accounts.models import AccountAccessState
    from apps.organizations.models import OrganizationMembership

    from .whatsapp.access import revoke

    challenge = issue(house)
    user = house["tenant"]
    if change == "expiry":
        NotificationPhoneLink.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    elif change == "password":
        user.set_password("changed-synthetic-password")
        user.save()
    elif change == "email":
        user.email = "changed@example.com"
        user.save()
        mark_email_verified(user)
    elif change == "unverified":
        AccountAccessState.objects.filter(user=user).update(verified_at=None)
    elif change == "suspended":
        user.is_active = False
        user.save()
    elif change == "role":
        OrganizationMembership.objects.filter(user=user).update(is_active=False)
    else:
        # Real STOP invalidates unconsumed challenges as well as bindings.
        revoke(user=user)
        base.incoming("STOP")
    response = confirm(house, challenge["id"])
    assert response.status_code in {400, 403}, response.content
    assert not WhatsAppBinding.objects.filter(revoked_at__isnull=True).exists()


def test_another_account_cannot_complete_or_spend_attempts(house):
    challenge = issue(house)
    assert confirm(house, challenge["id"], user=house["manager"]).status_code == 400
    assert NotificationPhoneLink.objects.get().failed_attempts == 0
    assert confirm(house, challenge["id"]).status_code == 200


def test_resend_cooldown_and_new_code_invalidates_old_challenge(house):
    old = issue(house)
    api = base.client(house["tenant"])
    with patch("apps.notifications.phone_codes.post_json") as send:
        assert api.post(URL, {"phone": base.PHONE}, format="json").status_code == 429
    send.assert_not_called()
    NotificationPhoneLink.objects.update(created_at=timezone.now() - timedelta(seconds=61))
    new = issue(house)
    assert confirm(house, old["id"]).status_code == 400
    assert confirm(house, new["id"]).status_code == 200


@pytest.mark.parametrize(
    "change", ["unapproved", "disabled", "restricted", "malformed", "anonymous"]
)
def test_no_send_without_configuration_valid_number_and_verified_account(house, settings, change):
    data = {"phone": base.PHONE}
    api = base.client(house["tenant"])
    if change == "unapproved":
        settings.APPROVED_WHATSAPP_TEMPLATES = []
    elif change == "disabled":
        settings.WHATSAPP_OTP_ENABLED = False
    elif change == "restricted":
        settings.OUTBOUND_PHONE_ALLOWLIST = []
    elif change == "malformed":
        data["phone"] = "bad"
    else:
        api = APIClient()
    with patch("apps.notifications.phone_codes.post_json") as send:
        response = api.post(URL, data, format="json")
    assert response.status_code in {400, 401, 403, 503}
    send.assert_not_called()
    assert not NotificationPhoneLink.objects.exists()


@pytest.mark.parametrize(
    "error, status",
    [
        (TimeoutError(), "review"),
        (ProviderRejected("http_500"), "review"),
        (ProviderRejected("http_400"), "failed"),
    ],
)
def test_transport_failures_are_not_retried_or_exposed(house, error, status):
    with patch("apps.notifications.phone_codes.post_json", side_effect=error) as send:
        response = base.client(house["tenant"]).post(URL, {"phone": base.PHONE}, format="json")
    assert response.status_code == (503 if status == "failed" else 202)
    assert send.call_count == 1
    assert NotificationPhoneLink.objects.get().delivery_status == status
    assert not WhatsAppBinding.objects.exists()


def test_user_rate_limit_stops_sixth_request(house):
    api = base.client(house["tenant"])
    with patch(
        "apps.notifications.phone_codes.post_json", return_value={"messages": [{"id": "fake"}]}
    ):
        for _ in range(5):
            NotificationPhoneLink.objects.update(created_at=timezone.now() - timedelta(seconds=61))
            assert api.post(URL, {"phone": base.PHONE}, format="json").status_code == 202
        assert api.post(URL, {"phone": base.PHONE}, format="json").status_code == 429
    cache.clear()
