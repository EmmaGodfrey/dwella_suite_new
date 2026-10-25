import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

import pytest
from django.db import close_old_connections, connection
from rest_framework.test import APIClient

from apps.billing.models import Payment

from .evidence import read_exchange
from .models import Collection, Exchange, Payout
from .provider import ProviderResult
from .services import reconcile_collection, start_checkout, submit_mobile_money
from .testing import client_for, collection_result, http_response

pytestmark = pytest.mark.django_db


def details(**changes):
    return {
        "amount": "100.00",
        "idempotency_key": str(uuid.uuid4()),
        "channel": "mobile-money",
        "phone": "0971111111",
        "operator": "mtn",
        **changes,
    }


def endpoint(home):
    return f"/api/v1/payments/tenant/invoices/{home['invoice'].public_id}/checkout/"


def make_mobile(home):
    return start_checkout(invoice=home["invoice"], user=home["tenant"], **details())


def result_for(row, state="pay-offline", **changes):
    return collection_result(
        row,
        state=state,
        settled=state == "successful",
        mobileMoneyDetails={"phone": "0971111111", "operator": "mtn", "country": "zm"},
        **changes,
    )


def test_native_request_once_keeps_evidence_and_waits_for_phone(home):
    payload = details()

    def response(request, **kwargs):
        row = Collection.objects.get()
        assert request.method == "POST"
        assert request.full_url.endswith("/collections/mobile-money")
        sent = json.loads(request.data)
        assert sent == {
            "reference": row.reference,
            "amount": 100.0,
            "phone": "+260971111111",
            "operator": "mtn",
            "country": "zm",
            "bearer": "merchant",
        }
        assert row.collection_submitted_at
        return http_response(json.dumps(result_for(row).payload).encode())

    with patch("apps.payments.provider.urllib.request.build_opener") as build:
        build.return_value.open.side_effect = response
        client = client_for(home["tenant"])
        for _ in range(2):
            response_data = client.post(endpoint(home), payload, format="json")
            assert response_data.status_code == 200, response_data.content
            data = response_data.json()["response_data"]
            assert data["checkout"] is None
            assert data["collection"]["status"] == "pending"
            assert data["collection"]["provider_status"] == "pay-offline"
            assert "payer_phone" not in data["collection"]
        assert build.return_value.open.call_count == 1
    assert not Payment.objects.exists() and not Payout.objects.exists()
    evidence = Exchange.objects.get(operation="collection_submit")
    assert read_exchange(evidence)["response"]["data"]["status"] == "pay-offline"


@pytest.mark.parametrize(
    "changes",
    [
        {"phone": "bad"},
        {"phone": ""},
        {"operator": ""},
        {"operator": "evil"},
        {"channel": "wire"},
        {"channel": "card"},
        {"amount": "0.001"},
        {"amount": "999999"},
    ],
)
def test_invalid_native_input_never_sends_request(home, changes):
    with patch("apps.payments.services.Provider") as provider:
        response = client_for(home["tenant"]).post(
            endpoint(home), details(**changes), format="json"
        )
        assert response.status_code == 400
        provider.assert_not_called()
    assert not Collection.objects.exists()


@pytest.mark.parametrize(
    "change",
    [{"phone": "0971111112"}, {"operator": "airtel"}, {"amount": "90.00"}, {"channel": "card"}],
)
def test_pending_inputs_and_idempotency_cannot_be_changed(home, change):
    row = make_mobile(home)
    payload = details(idempotency_key=str(row.idempotency_key), **change)
    if change.get("channel") == "card":
        payload.pop("phone")
        payload.pop("operator")
    with patch("apps.payments.services.Provider") as provider:
        assert (
            client_for(home["tenant"]).post(endpoint(home), payload, format="json").status_code
            == 400
        )
        payload["idempotency_key"] = str(uuid.uuid4())
        assert (
            client_for(home["tenant"]).post(endpoint(home), payload, format="json").status_code
            == 400
        )
        provider.assert_not_called()


def test_auth_isolation_and_throttling_before_native_debit(home):
    from django.contrib.auth import get_user_model

    outsider = get_user_model().objects.create_user(username="unrelated-native")
    with patch("apps.payments.services.Provider") as provider:
        for client in [APIClient(), client_for(home["manager"]), client_for(outsider)]:
            assert client.post(endpoint(home), details(), format="json").status_code in {
                401,
                403,
                404,
            }
        with patch("apps.payments.views.PaymentWriteThrottle.rate", "1/hour"):
            client = client_for(home["tenant"])
            assert client.post(endpoint(home), {}, format="json").status_code == 400
            assert client.post(endpoint(home), details(), format="json").status_code == 429
        provider.assert_not_called()


@pytest.mark.parametrize(
    "result", [ProviderResult({}, None, "network_error"), ProviderResult({}, 502, "invalid_json")]
)
def test_uncertain_submission_cannot_be_retried(home, result):
    row = make_mobile(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = result
        submit_mobile_money(row)
        submit_mobile_money(row)
        assert provider.return_value.request.call_count == 1
    row.refresh_from_db()
    assert row.status == "pending" and row.next_check_at and row.collection_submitted_at
    assert not Payment.objects.exists()


@pytest.mark.parametrize("state", ["successful", "failed"])
def test_native_authoritative_result_uses_existing_ledger_once(home, state):
    row = make_mobile(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = result_for(row, state)
        submit_mobile_money(row)
        reconcile_collection(row)
    row.refresh_from_db()
    assert row.status == state
    assert Payment.objects.count() == (1 if state == "successful" else 0)
    assert Payout.objects.count() == (1 if state == "successful" else 0)


@pytest.mark.parametrize(
    "changes",
    [
        {"type": "card"},
        {"mobileMoneyDetails": {"phone": "0971111112", "operator": "mtn", "country": "zm"}},
        {"mobileMoneyDetails": {"phone": "0971111111", "operator": "airtel", "country": "zm"}},
        {"mobileMoneyDetails": []},
    ],
)
def test_wrong_payer_cannot_credit_invoice(home, changes):
    row = make_mobile(home)
    result = collection_result(
        row,
        **{
            "mobileMoneyDetails": {"phone": "0971111111", "operator": "mtn", "country": "zm"},
            **changes,
        },
    )
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = result
        submit_mobile_money(row)
    row.refresh_from_db()
    assert row.status == "review" and not Payment.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_claim_commits_before_network_and_concurrent_submission_is_once(home):
    row = make_mobile(home)
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row-lock concurrency")
    barrier = Barrier(2)

    def submit():
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            submit_mobile_money(row)
        finally:
            close_old_connections()

    def response(*args, **kwargs):
        assert not connection.in_atomic_block
        assert Collection.objects.get(pk=row.pk).collection_submitted_at
        return result_for(row)

    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.side_effect = response
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _: submit(), range(2)))
        assert provider.return_value.request.call_count == 1


def test_card_is_local_and_restricted_to_card_checkout(home):
    with patch("apps.payments.services.Provider") as provider:
        response = client_for(home["tenant"]).post(
            endpoint(home),
            {"channel": "card", "amount": "100.00", "idempotency_key": str(uuid.uuid4())},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["response_data"]["checkout"]["channels"] == ["card"]
        provider.assert_not_called()


@pytest.mark.parametrize(
    "payment_type,expected", [("card", "successful"), ("mobile-money", "review")]
)
def test_card_result_must_match_chosen_channel(home, payment_type, expected):
    row = start_checkout(
        invoice=home["invoice"],
        user=home["tenant"],
        amount="100.00",
        idempotency_key=uuid.uuid4(),
        channel="card",
    )
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(row, type=payment_type)
        reconcile_collection(row)
    row.refresh_from_db()
    assert row.status == expected
    assert Payment.objects.count() == (1 if expected == "successful" else 0)
