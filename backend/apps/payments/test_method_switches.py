import time
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.models import TwoFactorDevice
from apps.accounts.security import _hotp, make_totp_secret
from apps.audit.models import AuditEvent, PlatformSettings

from .services import start_checkout
from .testing import client_for, home  # noqa: F401

pytestmark = pytest.mark.django_db
PASSWORD = "SwitchTestPassword42!"
URL = "/api/v1/payments/platform/switches/"


@pytest.fixture
def admin():
    cache.clear()
    user = get_user_model().objects.create_user(
        username="switch-admin", password=PASSWORD, is_staff=True, is_superuser=True
    )
    device = TwoFactorDevice.objects.create(user=user, secret=make_totp_secret(), is_confirmed=True)
    client = APIClient()
    client.force_authenticate(user)
    return client, device


def proof(device, **extra):
    return {
        "password": PASSWORD,
        "code": _hotp(device.secret, int(time.time() // 30)),
        **extra,
    }


def card_details():
    return {"amount": "100.00", "idempotency_key": str(uuid.uuid4()), "channel": "card"}


def test_switch_needs_password_and_fresh_authenticator_code(admin):
    client, device = admin
    wrong = client.post(URL, proof(device, card=False, password="nope"), format="json")
    assert wrong.status_code == 403
    assert not PlatformSettings.objects.filter(pk=1).exists() or (
        "payments_card_enabled" not in PlatformSettings.objects.get(pk=1).runtime_config
    )
    ok = client.post(URL, proof(device, card=False), format="json")
    assert ok.status_code == 200
    assert ok.json()["response_data"] == {"card": False, "mobile_money": True}
    # The same code cannot be replayed for another change.
    replay = client.post(URL, proof(device, mobile_money=False), format="json")
    assert replay.status_code == 403
    assert AuditEvent.objects.filter(action="platform.payment_methods_switched").count() == 1


def test_ordinary_settings_patch_cannot_change_money_switches(admin):
    client, _ = admin
    response = client.patch(
        "/api/v1/platform/runtime-settings/", {"payments_card_enabled": False}, format="json"
    )
    assert response.status_code == 400


def test_only_superusers_can_use_switches(admin):
    _, device = admin
    anonymous = APIClient().post(URL, proof(device, card=False), format="json")
    assert anonymous.status_code in (401, 403)

    ordinary_user = get_user_model().objects.create_user(
        username="ordinary-user", password=PASSWORD
    )
    ordinary_client = APIClient()
    ordinary_client.force_authenticate(ordinary_user)
    forbidden = ordinary_client.post(URL, proof(device, card=False), format="json")
    assert forbidden.status_code == 403
    assert not PlatformSettings.objects.filter(pk=1).exists()


@pytest.mark.parametrize(
    "payload",
    [
        {"card": False, "password": PASSWORD, "code": "123"},
        {"mobile_money": False, "password": PASSWORD, "code": "123456", "extra": True},
        {"password": PASSWORD, "code": "123456"},
    ],
)
def test_malformed_or_unsupported_switch_requests_are_rejected(admin, payload):
    client, _ = admin
    response = client.post(URL, payload, format="json")
    assert response.status_code == 400
    assert not PlatformSettings.objects.filter(pk=1).exists()


def test_invalid_authenticator_code_is_rejected_without_changing_switches(admin):
    client, device = admin
    stale_code = _hotp(device.secret, int(time.time() // 30) + 10)
    response = client.post(URL, proof(device, card=False, code=stale_code), format="json")
    assert response.status_code == 403
    assert not PlatformSettings.objects.filter(pk=1).exists()


def test_switch_endpoint_is_throttled(admin):
    client, device = admin
    payload = proof(device, card=False, password="wrong-password")
    responses = [client.post(URL, payload, format="json") for _ in range(11)]
    assert all(response.status_code == 403 for response in responses[:10])
    assert responses[-1].status_code == 429
    assert not PlatformSettings.objects.filter(pk=1).exists()


def test_card_off_blocks_card_checkout_but_not_mobile_money(admin, home):  # noqa: F811
    client, device = admin
    client.post(URL, proof(device, card=False), format="json")
    with pytest.raises(Exception, match="Card payments are switched off"):
        start_checkout(invoice=home["invoice"], user=home["tenant"], **card_details())
    options = (
        client_for(home["tenant"])
        .get("/api/v1/payments/tenant/options/")
        .json()["response_data"]
    )
    assert options["methods"] == {"card": False, "mobile_money": True}
    assert options["enabled"] is True
    row = start_checkout(
        invoice=home["invoice"],
        user=home["tenant"],
        amount="100.00",
        idempotency_key=str(uuid.uuid4()),
        channel="mobile-money",
        phone="0971111111",
        operator="mtn",
    )
    assert row.channel == "mobile-money"
