"""Replacements are picked up by messaging consumers without worker restarts."""

import json
from unittest.mock import patch

import pytest
from django.db import connections
from rest_framework.test import APIClient

from .models import ProviderCredential
from .test_provider_credentials import SECRET, URL, body
from .test_provider_credentials import admin as admin_fixture

pytestmark = pytest.mark.django_db
admin = admin_fixture


@pytest.fixture(autouse=True)
def close_quota_connection():
    yield
    connections["email_quota"].close()


def test_credentials_are_used_by_sms_and_webhook_verification(admin, settings):
    from apps.notifications.phone_messaging import send_sms

    client, _, device = admin
    assert client.post(URL, body(device), format="json").status_code == 200
    row = type("Delivery", (), {"recipient": "+260970000001", "subject": "Test", "body": "Hello"})()
    response = {
        "SMSMessageData": {
            "Recipients": [
                {"number": row.recipient, "statusCode": 100, "messageId": "live-accepted"}
            ]
        }
    }
    with patch("apps.notifications.phone_messaging.post_form", return_value=response) as send:
        assert send_sms(row, {"sms_sender_id": "Dwella"}) == "live-accepted"
    assert send.call_args.args[2]["apiKey"] == SECRET


@pytest.mark.django_db(transaction=True, databases=["default", "email_quota"])
def test_resend_and_meta_use_replacements_instead_of_environment_values(admin, settings):
    from django.core.mail import EmailMessage

    from apps.common.email_router import EmailBackend

    from .provider_credentials import cipher

    values = {
        "RESEND_API_KEY": "re_synthetic_replacement_12345678",
        "WHATSAPP_VERIFY_TOKEN": "replacement-verify-token-123456789012345",
    }
    for name, value in values.items():
        ProviderCredential.objects.create(
            name=name,
            encrypted_value=cipher().encrypt(json.dumps({"name": name, "value": value}).encode()),
        )
    settings.EMAIL_PROVIDER_ORDER = ["resend"]
    settings.EMAIL_PRIMARY_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.RESEND_FROM_EMAIL = "verified@example.com"
    with patch(
        "apps.common.email_router.post_json", return_value={"id": "synthetic-mail-id"}
    ) as send:
        assert (
            EmailBackend().send_messages(
                [EmailMessage("Test", "Message", to=["recipient@example.com"])]
            )
            == 1
        )
        assert send.call_args.args[2]["Authorization"] == "Bearer " + values["RESEND_API_KEY"]
    client = APIClient()
    response = client.get(
        "/api/v1/notifications/webhooks/whatsapp/",
        {
            "hub.mode": "subscribe",
            "hub.verify_token": values["WHATSAPP_VERIFY_TOKEN"],
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200, response.content
    assert response.content == b"12345"
