from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.organizations.models import Organization, OrganizationMembership

from .models import Destination
from .provider import ProviderResult
from .testing import checkout, client_for

pytestmark = pytest.mark.django_db
URL = "/api/v1/payments/destination/"
CHECK = "/api/v1/payments/destination/check/"
PASSWORD = "Receiving-pass-2026"
DETAILS = {
    "phone": "0972222222",
    "operator": "mtn",
    "confirm_details": True,
    "password": PASSWORD,
}
BANK = {
    "kind": "bank-account",
    "bank_id": "bank-zanaco",
    "account_number": "0921445509210",
    "confirm_details": True,
    "password": PASSWORD,
}
BANKS = ProviderResult(
    {"status": True, "data": [{"id": "bank-zanaco", "name": "Zanaco", "country": "zm"}]}, 200
)


def found(name="MUTALE BANDA"):
    return ProviderResult({"status": True, "data": {"accountName": name}}, 200)


NOT_FOUND = ProviderResult({"status": False, "message": "Account not found", "data": None}, 400)
DOWN = ProviderResult({}, None, "network_error")


@pytest.fixture(autouse=True)
def manager_password(home):
    home["manager"].set_password(PASSWORD)
    home["manager"].save()


def lenco(*responses):
    """Patch Lenco for the receiving-account lookups; returns the mock."""
    patcher = patch("apps.payments.withdrawals.Provider")
    provider = patcher.start()
    provider.return_value.request.side_effect = list(responses)
    return patcher, provider


def post(client, url, body, *responses):
    patcher, provider = lenco(*responses)
    try:
        return client.post(url, body, format="json"), provider
    finally:
        patcher.stop()


def test_lenco_name_is_saved_and_started_payments_keep_their_account(home):
    original = home["destination"]
    collection = checkout(home)
    client = client_for(home["manager"])
    response, provider = post(client, URL, DETAILS, found())
    assert response.status_code == 200
    data = response.json()["response_data"]
    assert data["phone"] == "+260972222222" and data["account_name"] == "MUTALE BANDA"
    assert data["checked_with_lenco"] is True and data["kind"] == "mobile-money"
    operation = provider.return_value.request.call_args
    assert operation.args == ("resolve_mobile_money",)
    assert operation.kwargs["payload"] == {
        "phone": "0972222222",
        "operator": "mtn",
        "country": "zm",
    }
    # Saving the same details again is not a new version.
    assert post(client, URL, DETAILS, found())[0].status_code == 200
    assert Destination.objects.filter(organization=home["org"]).count() == 2
    active = Destination.objects.get(organization=home["org"], enabled=True)
    assert active.approved_by == home["manager"] and active.lookup_name == "MUTALE BANDA"
    original.refresh_from_db()
    collection.refresh_from_db()
    assert not original.enabled and collection.destination_id == original.pk
    assert AuditEvent.objects.filter(action="payment.destination_saved").exists()


def test_check_shows_the_registered_name_without_saving(home):
    client = client_for(home["manager"])
    body = {key: DETAILS[key] for key in ("phone", "operator")}
    response, _ = post(client, CHECK, body, found())
    assert response.json()["response_data"] == {
        "found": True,
        "account_name": "MUTALE BANDA",
        "bank_name": "",
    }
    response, _ = post(client, CHECK, body, NOT_FOUND)
    assert response.json()["response_data"]["found"] is False
    assert Destination.objects.get(organization=home["org"], enabled=True) == home["destination"]


def test_bank_account_uses_the_bank_list_and_lookup(home):
    client = client_for(home["manager"])
    response, provider = post(client, URL, BANK, BANKS, found("MUTALE BANDA"))
    assert response.status_code == 200
    data = response.json()["response_data"]
    assert data["kind"] == "bank-account" and data["bank_name"] == "Zanaco"
    assert data["account_suffix"] == "9210" and data["phone"] == ""
    lookup = provider.return_value.request.call_args
    assert lookup.args == ("resolve_bank_account",)
    assert lookup.kwargs["payload"]["accountNumber"] == "0921445509210"
    # The bank list is cached; an unknown bank is refused before Lenco is asked.
    response, provider = post(client, URL, {**BANK, "bank_id": "unknown"})
    assert response.status_code == 400
    provider.return_value.request.assert_not_called()


@pytest.mark.parametrize("answer", [NOT_FOUND, DOWN])
def test_unconfirmed_accounts_are_refused_outside_the_test_bypass(home, answer):
    response, _ = post(client_for(home["manager"]), URL, DETAILS, answer)
    assert response.status_code == 400
    assert Destination.objects.get(organization=home["org"], enabled=True) == home["destination"]


def test_test_bypass_saves_the_entered_name_only_when_lenco_cannot_answer(home, settings):
    settings.APP_ENVIRONMENT = "test"
    settings.LENCO_ALLOW_UNVERIFIED_DESTINATIONS = True
    client = client_for(home["manager"])
    assert post(client, URL, DETAILS, DOWN)[0].status_code == 400  # name required
    body = {**DETAILS, "account_name": "Test receiver"}
    assert post(client, URL, body, NOT_FOUND)[0].status_code == 400
    response, _ = post(client, URL, body, DOWN)
    assert response.status_code == 200
    row = Destination.objects.get(organization=home["org"], enabled=True)
    assert row.account_name == "Test receiver" and row.lookup_name == ""


def test_a_malformed_lenco_key_is_a_clear_refusal_not_a_crash(home, settings):
    settings.LENCO_SECRET_KEY = "short"
    client = client_for(home["manager"])
    response = client.post(CHECK, {k: DETAILS[k] for k in ("phone", "operator")}, format="json")
    assert response.status_code == 400
    settings.APP_ENVIRONMENT = "test"
    settings.LENCO_ALLOW_UNVERIFIED_DESTINATIONS = True
    response = client.post(CHECK, {k: DETAILS[k] for k in ("phone", "operator")}, format="json")
    assert response.status_code == 200
    assert response.json()["response_data"]["found"] is None


def test_password_and_authenticator_code_are_required(home):
    from apps.accounts.models import TwoFactorDevice

    client = client_for(home["manager"])
    response, provider = post(client, URL, {**DETAILS, "password": "wrong"})
    assert response.status_code == 400 and "password" in str(response.json())
    provider.return_value.request.assert_not_called()
    TwoFactorDevice.objects.create(
        user=home["manager"], secret="JBSWY3DPEHPK3PXP", is_confirmed=True
    )
    assert post(client, URL, DETAILS)[0].status_code == 400
    with patch("apps.accounts.security.verify_totp", return_value=True):
        response, _ = post(client, URL, {**DETAILS, "code": "123456"}, found())
    assert response.status_code == 200


@pytest.mark.parametrize(
    "changes",
    [
        {"phone": "bad"},
        {"phone": "+441234567890"},
        {"operator": "other"},
        {"operator": ""},
        {"confirm_details": False},
        {"confirm_details": None},
        {"password": ""},
        {"kind": "card"},
        {"kind": "bank-account"},
        {"kind": "bank-account", "bank_id": "bank-zanaco", "account_number": "12ab34567"},
    ],
)
def test_bad_input_cannot_replace_the_destination(home, changes):
    response, _ = post(client_for(home["manager"]), URL, {**DETAILS, **changes}, found())
    assert response.status_code == 400
    assert Destination.objects.get(organization=home["org"], enabled=True) == home["destination"]


def test_access_is_scoped_and_tenant_and_admin_cannot_save(home):
    assert APIClient().post(URL, DETAILS, format="json").status_code in (401, 403)
    for user in (home["tenant"], home["admin"]):
        assert post(client_for(user), URL, DETAILS, found())[0].status_code == 403
    other = Organization.objects.create(name="Separate receiving workspace")
    manager = get_user_model().objects.create_user(
        username="other-destination-manager", password=PASSWORD
    )
    OrganizationMembership.objects.create(organization=other, user=manager, role="landlord")
    response, _ = post(
        client_for(manager),
        URL,
        {**DETAILS, "organization_id": str(home["org"].public_id)},
        found(),
    )
    assert response.status_code == 200
    assert Destination.objects.get(organization=home["org"], enabled=True) == home["destination"]
    assert Destination.objects.get(organization=other, enabled=True).approved_by == manager


def test_currency_suspension_and_revocation_are_enforced(home):
    client = client_for(home["manager"])
    org = home["org"]
    org.currency = "USD"
    org.save()
    assert post(client, URL, DETAILS, found())[0].status_code == 400
    org.currency, org.is_active = "ZMW", False
    org.save()
    assert post(client, URL, DETAILS, found())[0].status_code == 403
    org.is_active = True
    org.save()
    OrganizationMembership.objects.filter(user=home["manager"]).update(is_active=False)
    assert post(client, URL, DETAILS, found())[0].status_code == 403


def test_destination_writes_are_throttled(home):
    from .views import PaymentWriteThrottle

    cache.clear()
    with patch.object(PaymentWriteThrottle, "rate", "1/hour"):
        client = client_for(home["manager"])
        assert post(client, URL, DETAILS, found())[0].status_code == 200
        assert post(client, URL, DETAILS, found())[0].status_code == 429
