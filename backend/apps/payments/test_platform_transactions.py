import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent

from .evidence import record_exchange
from .models import Collection, Payout, ProviderAccount, ProviderTransaction, Withdrawal
from .testing import ACCOUNT, SECRET, checkout, client_for

pytestmark = pytest.mark.django_db
URL = "/api/v1/payments/platform/transactions/"


def test_transaction_browsing_is_superuser_only_and_read_only(home):
    row = checkout(home)
    for client in [
        APIClient(),
        client_for(home["tenant"]),
        client_for(home["manager"]),
        client_for(get_user_model().objects.create_user(username="staff", is_staff=True)),
    ]:
        for path in [
            URL,
            "/api/v1/payments/platform/configuration/",
            f"/api/v1/payments/platform/collections/{row.public_id}/",
        ]:
            assert client.get(path).status_code in {401, 403}
    with patch("apps.payments.provider.Provider.request") as network:
        client = client_for(home["admin"])
        response = client.get(URL)
        assert response.status_code == 200
        assert response["Cache-Control"] == "private, no-store"
        assert SECRET not in response.content.decode()
        assert client.post(URL, {}, format="json").status_code == 405
        config = client.get("/api/v1/payments/platform/configuration/")
        assert config.json()["response_data"]["api_configured"]
        assert SECRET not in config.content.decode()
        balance = client.get("/api/v1/payments/platform/balance/").json()["response_data"]
        assert balance["environment"] == "sandbox" and balance["currency"] == "ZMW"
        network.assert_not_called()


def test_transaction_filters_and_validation(home):
    row = checkout(home)
    client = client_for(home["admin"])
    assert len(client.get(URL, {"search": row.reference}).json()["response_data"]) == 1
    assert client.get(URL, {"environment": "live"}).json()["response_data"] == []
    assert client.get(URL, {"status": "failed"}).json()["response_data"] == []
    for filters in [
        {"kind": "unknown"},
        {"status": "not-real"},
        {"workspace": "no"},
        {"from_date": "bad"},
        {"from_date": "2026-10-26", "until_date": "2026-01-01"},
    ]:
        assert client.get(URL, filters).status_code == 400


def test_metadata_lists_do_not_load_encrypted_bodies_and_evidence_is_audited(home):
    row = checkout(home)
    payout = Payout.objects.create(collection=row, amount="90")
    exchange = record_exchange(
        environment="sandbox",
        operation="payout_submit",
        payout=payout,
        body=b'{"status":"pending","token":"secret-value"}',
    )
    client = client_for(home["admin"])
    with CaptureQueriesContext(connection) as queries:
        response = client.get(f"/api/v1/payments/platform/collections/{row.public_id}/exchanges/")
    assert response.status_code == 200
    assert str(exchange.public_id) in response.content.decode()
    assert not any("encrypted_payload" in q["sql"].lower() for q in queries)
    evidence = client.get(f"/api/v1/payments/platform/exchanges/{exchange.public_id}/")
    assert evidence.status_code == 200 and "secret-value" not in evidence.content.decode()
    assert AuditEvent.objects.filter(action="payment.evidence_viewed").exists()


@pytest.mark.parametrize("kind", ["collections", "payouts", "withdrawals", "ledger"])
def test_query_count_does_not_grow_with_page_size(home, kind):
    for index in range(12):
        row = Collection.objects.create(
            organization=home["org"],
            invoice=home["invoice"],
            initiated_by=home["tenant"],
            destination=home["destination"],
            environment="sandbox",
            idempotency_key=uuid.uuid4(),
            amount="100",
            status="successful",
            debit_account_id=ACCOUNT,
            provider_id=f"collection-{index}",
        )
        Payout.objects.create(collection=row, amount="90", provider_id=f"payout-{index}")
        Withdrawal.objects.create(
            organization=home["org"],
            destination=home["destination"],
            requested_by=home["manager"],
            environment="sandbox",
            debit_account_id=ACCOUNT,
            idempotency_key=uuid.uuid4(),
            amount="40",
            fee_reserved="12",
            provider_id=f"withdrawal-{index}",
        )
        exchange = record_exchange(environment="sandbox", operation="ledger_page", body=b"{}")
        ProviderTransaction.objects.create(
            account=ProviderAccount.objects.get(),
            provider_id=row.provider_id,
            kind="credit",
            amount="100",
            posted_at=timezone.now(),
            content_digest="a" * 64,
            exchange=exchange,
        )
    client = client_for(home["admin"])
    counts = []
    for page_size in [1, 12]:
        with CaptureQueriesContext(connection) as queries:
            response = client.get(URL, {"kind": kind, "page_size": page_size})
        assert response.status_code == 200
        assert len(response.json()["response_data"]) == page_size
        assert not any("encrypted_payload" in q["sql"].lower() for q in queries)
        counts.append(len(queries))
    assert counts[0] == counts[1]
