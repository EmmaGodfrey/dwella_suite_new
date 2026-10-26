# ruff: noqa: F811
import hashlib
import hmac
import json
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from apps.common.provider_http import ProviderRejected
from apps.payments.testing import client_for, home  # noqa: F401

from .messaging import dispatch_messages
from .models import MessageDelivery, NotificationPreferences, PhoneMessagingConsent
from .phone_messaging import normalize_phone, phone_block, save_user_consent, send_whatsapp

pytestmark = pytest.mark.django_db
URL = "/api/v1/notifications/webhooks/whatsapp/"


@pytest.fixture(autouse=True)
def configuration(settings):
    cache.clear()
    settings.WHATSAPP_ENABLED = True
    settings.WHATSAPP_ACCESS_TOKEN = "test-access-token"
    settings.WHATSAPP_PHONE_NUMBER_ID = "phone-id"
    settings.WHATSAPP_BUSINESS_ACCOUNT_ID = "business-id"
    settings.WHATSAPP_APP_SECRET = "test-app-secret"
    settings.WHATSAPP_VERIFY_TOKEN = "test-verify-token"
    settings.WHATSAPP_RENT_TEMPLATE = "dwella_rent_reminder"
    settings.OUTBOUND_PHONE_ALLOWLIST = []
    settings.APP_ENVIRONMENT = "production"


def delivery(home, **changes):
    tenant = home["invoice"].tenant
    tenant.phone_number = "+260970000111"
    tenant.save()
    NotificationPreferences.objects.update_or_create(
        user=home["tenant"],
        defaults={"whatsapp_enabled": True},
    )
    save_user_consent(home["tenant"], {"whatsapp_enabled": True})
    return MessageDelivery.objects.create(
        organization=home["org"],
        tenant=tenant,
        channel="whatsapp",
        recipient=tenant.phone_number,
        subject="Rent notice",
        body="Reminder",
        identity="test-wa",
        status="queued",
        available_at=timezone.now() - timedelta(days=1),
        **changes,
    )


def callback(value, *, signature=True, business="business-id", phone="phone-id"):
    body = json.dumps(
        {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": business,
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "metadata": {"phone_number_id": phone},
                                **value,
                            },
                        }
                    ],
                }
            ],
        }
    ).encode()
    digest = hmac.new(b"test-app-secret", body, hashlib.sha256).hexdigest()
    return APIClient().post(
        URL,
        body,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256="sha256=" + digest if signature else "fake",
    )


def status_event(row, status="delivered", stamp=None):
    return {
        "id": "wamid.1",
        "status": status,
        "recipient_id": normalize_phone(row.recipient)[1:],
        "timestamp": str(int((stamp or timezone.now()).timestamp())),
        "biz_opaque_callback_data": str(row.public_id),
    }


def test_verification_challenge_and_wrong_or_missing_token():
    client = APIClient()
    query = {"hub.mode": "subscribe", "hub.challenge": "12345", "hub.verify_token": "bad"}
    assert client.get(URL, query).status_code == 403
    query["hub.verify_token"] = "test-verify-token"
    response = client.get(URL, query)
    assert response.status_code == 200 and response.content == b"12345"
    query["hub.challenge"] = "<script>"
    assert client.get(URL, query).status_code == 400


def test_unsigned_invalid_and_wrong_account_events_cannot_change_delivery(home):
    row = delivery(home, provider="whatsapp", provider_id="wamid.1")
    assert callback({"statuses": [status_event(row)]}, signature=False).status_code == 403
    assert callback({"statuses": [status_event(row)]}, business="foreign").status_code == 200
    assert callback({"statuses": [status_event(row)]}, phone="foreign").status_code == 200
    assert callback({"statuses": [None]}).status_code == 400
    row.refresh_from_db()
    assert row.status == "queued" and row.delivered_at is None


def test_delivery_read_duplicate_and_out_of_order_callback_before_send_response(home):
    row = delivery(home)
    row.status = "sending"
    row.save()
    now = timezone.now() - timedelta(seconds=4)
    delivered = {"statuses": [status_event(row, stamp=now)]}
    assert callback(delivered).status_code == 200
    assert callback(delivered).status_code == 200
    assert (
        callback({"statuses": [status_event(row, "read", now + timedelta(seconds=1))]}).status_code
        == 200
    )
    assert (
        callback({"statuses": [status_event(row, "sent", now - timedelta(seconds=1))]}).status_code
        == 200
    )
    row.refresh_from_db()
    assert row.status == "read" and row.delivered_at and row.read_at
    assert row.provider_id == "wamid.1"


def test_failure_details_and_wrong_recipient(home):
    row = delivery(home, provider="whatsapp", provider_id="wamid.1")
    row.status = "sent"
    row.save()
    event = status_event(row, "failed")
    event["recipient_id"] = "260970000999"
    assert callback({"statuses": [event]}).status_code == 200
    row.refresh_from_db()
    assert row.status == "sent"
    event["recipient_id"] = normalize_phone(row.recipient)[1:]
    event["errors"] = [{"code": 131047, "message": "Private provider detail"}]
    assert callback({"statuses": [event]}).status_code == 200
    row.refresh_from_db()
    assert row.status == "failed" and row.failure_code == "131047"


def test_stop_revokes_exact_number_and_settings_show_opt_out(home):
    row = delivery(home)
    consent = PhoneMessagingConsent.objects.get()
    consent.granted_at = timezone.now() - timedelta(minutes=2)
    consent.save()
    incoming = {
        "from": row.recipient[1:],
        "type": "text",
        "text": {"body": "STOP"},
        "timestamp": str(int(timezone.now().timestamp())),
    }
    assert callback({"messages": [incoming]}).status_code == 200
    assert callback({"messages": [incoming]}).status_code == 200
    row.refresh_from_db()
    consent.refresh_from_db()
    assert row.status == "cancelled" and not consent.allowed and consent.revoked_at
    response = client_for(home["tenant"]).get("/api/v1/notifications/preferences/")
    assert not response.json()["response_data"]["preferences"]["whatsapp_enabled"]
    assert "STOP" not in str(consent.__dict__)


def test_personal_consent_only_applies_to_current_linked_phone_and_channel(home):
    row = delivery(home)
    client = client_for(home["tenant"])
    assert (
        client.patch(
            "/api/v1/notifications/preferences/",
            {
                "sms_enabled": True,
                "phone": "+260970000999",
            },
            format="json",
        ).status_code
        == 400
    )
    assert (
        client.patch(
            "/api/v1/notifications/preferences/",
            {
                "sms_enabled": False,
            },
            format="json",
        ).status_code
        == 200
    )
    assert not PhoneMessagingConsent.objects.get(channel="sms").allowed
    row.recipient = "+260970000222"
    assert phone_block(row, timezone.now()) == "recipient_opted_out"


def test_delayed_stop_still_revokes_but_stop_before_explicit_reoptin_does_not(home):
    row = delivery(home)
    now = timezone.now()
    PhoneMessagingConsent.objects.update(
        granted_at=now - timedelta(minutes=5),
        last_inbound_at=now - timedelta(seconds=1),
    )
    incoming = {
        "from": row.recipient[1:],
        "type": "text",
        "text": {"body": "STOP"},
        "timestamp": str(int((now - timedelta(minutes=1)).timestamp())),
    }
    assert callback({"messages": [incoming]}).status_code == 200
    assert not PhoneMessagingConsent.objects.get().allowed
    save_user_consent(home["tenant"], {"whatsapp_enabled": True})
    row.status = "queued"
    row.save()
    assert callback({"messages": [incoming]}).status_code == 200
    assert PhoneMessagingConsent.objects.get().allowed
    row.refresh_from_db()
    assert row.status == "queued"


def test_template_window_consent_test_allowlist_and_disabled_configuration(home, settings):
    row = delivery(home)
    assert phone_block(row, timezone.now()) == "whatsapp_reply_window_closed"
    row.invoice = home["invoice"]
    assert phone_block(row, timezone.now()) == ""
    settings.WHATSAPP_RENT_TEMPLATE = ""
    assert phone_block(row, timezone.now()) == "whatsapp_template_required"
    settings.APP_ENVIRONMENT = "test"
    assert phone_block(row, timezone.now()) == "recipient_restricted"
    settings.OUTBOUND_PHONE_ALLOWLIST = [row.recipient]
    settings.WHATSAPP_RENT_TEMPLATE = "rent_template"
    with patch(
        "apps.notifications.phone_messaging.post_json", return_value={"messages": [{"id": "wa-1"}]}
    ) as api:
        assert send_whatsapp(row) == "wa-1"
    payload = api.call_args.args[1]
    assert payload["type"] == "template" and payload["template"]["name"] == "rent_template"
    assert len(payload["template"]["components"][0]["parameters"]) == 5


@pytest.mark.parametrize(
    "failure,expected", [(ProviderRejected("http_400"), "failed"), (TimeoutError(), "review")]
)
def test_dispatch_rejection_and_uncertainty_never_retry(home, failure, expected):
    row = delivery(home)
    PhoneMessagingConsent.objects.update(last_inbound_at=timezone.now())
    with patch("apps.notifications.messaging.send_whatsapp", side_effect=failure) as send:
        assert dispatch_messages(now=timezone.now().replace(hour=12)) == 0
        assert dispatch_messages(now=timezone.now().replace(hour=12)) == 0
    assert send.call_count == 1
    row.refresh_from_db()
    assert row.status == expected


def test_dispatch_rechecks_optout_after_claim_before_contacting_provider(home):
    from . import messaging

    row = delivery(home)
    PhoneMessagingConsent.objects.update(last_inbound_at=timezone.now())
    claim = messaging.claim

    def opt_out_after_claim(*args):
        result = claim(*args)
        PhoneMessagingConsent.objects.update(allowed=False)
        return result

    with patch.object(messaging, "claim", side_effect=opt_out_after_claim):
        with patch.object(messaging, "send_whatsapp") as send:
            assert dispatch_messages(now=timezone.now().replace(hour=12)) == 0
    send.assert_not_called()
    row.refresh_from_db()
    assert row.status == "cancelled" and row.reason == "recipient_opted_out"


def test_callback_rate_limit_and_malformed_signed_body(settings):
    with patch("apps.notifications.provider_webhooks.CallbackThrottle.rate", "1/min"):
        assert callback({}).status_code == 200
        assert callback({}).status_code == 429
    cache.clear()
    body = b"[]"
    digest = hmac.new(b"test-app-secret", body, hashlib.sha256).hexdigest()
    assert (
        APIClient()
        .post(
            URL, body, content_type="application/json", HTTP_X_HUB_SIGNATURE_256="sha256=" + digest
        )
        .status_code
        == 400
    )


def test_consent_table_uses_postgres_default_deny_row_security(home):
    from django.db import connection

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row security required.")
    delivery(home)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relrowsecurity FROM pg_class WHERE relname = %s",
            ["notifications_phonemessagingconsent"],
        )
        assert cursor.fetchone() == (True,)
