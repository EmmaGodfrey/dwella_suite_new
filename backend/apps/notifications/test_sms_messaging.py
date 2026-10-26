# ruff: noqa: F811
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.common.provider_http import ProviderRejected
from apps.payments.testing import client_for, home  # noqa: F401

from .messaging import channel_readiness, dispatch_messages
from .models import MessageDelivery, PhoneMessagingConsent
from .phone_messaging import save_user_consent, send_sms
from .test_phone_messaging import delivery

pytestmark = pytest.mark.django_db
BASE = "/api/v1/notifications/webhooks/sms/"
TOKEN = "test-callback-token-at-least-32-characters"


@pytest.fixture(autouse=True)
def configuration(settings):
    cache.clear()
    settings.SMS_ENABLED = True
    settings.AFRICASTALKING_USERNAME = "sandbox"
    settings.AFRICASTALKING_API_KEY = "test-api-key"
    settings.AFRICASTALKING_SENDER_ID = "Dwella"
    settings.AFRICASTALKING_CALLBACK_TOKEN = TOKEN
    settings.AFRICASTALKING_SANDBOX = True
    settings.APP_ENVIRONMENT = "production"
    settings.OUTBOUND_PHONE_ALLOWLIST = []


def sms_delivery(home):
    row = delivery(home)
    row.channel = "sms"
    row.save()
    save_user_consent(home["tenant"], {"sms_enabled": True})
    return row


def callback(kind, data, token=TOKEN):
    return APIClient().post(BASE + f"{kind}/?token={token}", data)


def test_sms_readiness_requires_explicit_enable_credentials_and_registered_sender(settings):
    assert channel_readiness()["sms"]
    for field, value in [
        ("SMS_ENABLED", False),
        ("AFRICASTALKING_SENDER_ID", ""),
        ("AFRICASTALKING_CALLBACK_TOKEN", "short"),
    ]:
        original = getattr(settings, field)
        setattr(settings, field, value)
        assert not channel_readiness()["sms"]
        setattr(settings, field, original)


def test_sms_send_payload_sandbox_and_acceptance_is_not_handset_delivery(home):
    row = sms_delivery(home)
    result = {
        "SMSMessageData": {
            "Recipients": [
                {
                    "number": row.recipient,
                    "messageId": "AT-1",
                    "statusCode": 101,
                }
            ]
        }
    }
    with patch("apps.notifications.phone_messaging.post_form", return_value=result) as api:
        assert dispatch_messages(now=timezone.now().replace(hour=12)) == 1
    row.refresh_from_db()
    assert row.provider == "africastalking" and row.status == "sent"
    assert row.provider_id == "AT-1" and row.delivered_at is None
    assert api.call_args.args[0] == "https://api.sandbox.africastalking.com/version1/messaging"
    payload = api.call_args.args[1]
    assert payload["from"] == "Dwella" and "Opt out:" in payload["message"]


def test_sms_http_200_recipient_rejection_is_a_failure(home):
    row = sms_delivery(home)
    result = {
        "SMSMessageData": {
            "Recipients": [
                {
                    "number": row.recipient,
                    "statusCode": 403,
                    "messageId": "rejected",
                }
            ]
        }
    }
    with patch("apps.notifications.phone_messaging.post_form", return_value=result):
        with pytest.raises(ProviderRejected, match="at_403"):
            send_sms(row)


def test_delivery_requires_callback_credentials_and_handles_out_of_order_duplicates(home):
    row = sms_delivery(home)
    row.status, row.provider, row.provider_id = "sent", "africastalking", "AT-1"
    row.save()
    body = {"id": "AT-1", "status": "Success", "phoneNumber": row.recipient}
    assert callback("delivery", body, token="wrong").status_code == 403
    assert callback("delivery", body).status_code == 200
    assert callback("delivery", body).status_code == 200
    assert callback("delivery", {**body, "status": "Submitted"}).status_code == 200
    assert callback("delivery", {**body, "status": "Failed"}).status_code == 200
    row.refresh_from_db()
    assert row.status == "delivered" and row.delivered_at and not row.failure_code
    assert callback("delivery", {**body, "phoneNumber": "+260970000999"}).status_code == 400
    assert callback("delivery", {**body, "status": "invented"}).status_code == 400


def test_optout_callback_and_settings_cancel_sms_without_affecting_whatsapp(home):
    row = sms_delivery(home)
    assert (
        callback(
            "opt-out",
            {
                "phoneNumber": row.recipient,
                "senderId": "foreign",
            },
        ).status_code
        == 400
    )
    assert (
        callback(
            "opt-out",
            {
                "phoneNumber": row.recipient,
                "senderId": "Dwella",
            },
        ).status_code
        == 200
    )
    assert not PhoneMessagingConsent.objects.get(channel="sms").allowed
    assert PhoneMessagingConsent.objects.get(channel="whatsapp").allowed
    row.refresh_from_db()
    assert row.status == "cancelled"
    data = client_for(home["tenant"]).get("/api/v1/notifications/preferences/").json()
    assert not data["response_data"]["preferences"]["sms_enabled"]


def test_delivery_before_response_requests_retry_without_persisting_unknown_history(home):
    row = sms_delivery(home)
    row.status, row.claimed_at = "sending", timezone.now()
    row.save()
    assert callback("delivery", {"id": "AT-1", "status": "Success"}).status_code == 503
    assert MessageDelivery.objects.count() == 1
    row.provider, row.provider_id = "africastalking", "AT-1"
    row.save()
    assert callback("delivery", {"id": "AT-1", "status": "Success"}).status_code == 200


def test_sms_stop_incoming_and_other_messages_do_not_create_chat_history(home):
    row = sms_delivery(home)
    data = {"from": row.recipient, "to": "Dwella", "text": "Hello"}
    assert callback("incoming", data).status_code == 200
    assert PhoneMessagingConsent.objects.get(channel="sms").allowed
    assert callback("incoming", {**data, "text": "STOP"}).status_code == 200
    assert not PhoneMessagingConsent.objects.get(channel="sms").allowed
    assert MessageDelivery.objects.count() == 1


def test_admin_message_list_query_count_does_not_grow_per_delivery(home):
    row = sms_delivery(home)
    client = client_for(home["admin"])
    url = "/api/v1/notifications/platform-messages/"
    with CaptureQueriesContext(connection) as small:
        assert client.get(url).status_code == 200
    MessageDelivery.objects.bulk_create(
        [
            MessageDelivery(
                organization=home["org"],
                tenant=row.tenant,
                channel="sms",
                recipient=row.recipient,
                subject="Notice",
                body="Body",
                identity=f"page-{i}",
                available_at=timezone.now() - timedelta(days=1),
            )
            for i in range(24)
        ]
    )
    with CaptureQueriesContext(connection) as full:
        response = client.get(url)
        assert response.status_code == 200
    assert len(full) == len(small), (len(small), len(full))
