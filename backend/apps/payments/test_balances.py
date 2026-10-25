import json
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.db import connection, transaction

from .balances import sync_balance
from .evidence import record_exchange
from .models import BalanceSnapshot, ProviderAccount, ProviderTransaction
from .provider import ProviderResult
from .testing import ACCOUNT

pytestmark = pytest.mark.django_db


def entry(identifier="txn-1", amount="100.00", kind="credit"):
    return {
        "id": identifier,
        "amount": amount,
        "type": kind,
        "accountId": ACCOUNT,
        "datetime": "2026-10-25T10:00:00Z",
    }


def provider_page(data, *, count=1):
    body = {"status": True, "data": data, "meta": {"pageCount": count}}
    evidence = record_exchange(
        environment="sandbox", operation="test_feed", body=json.dumps(body).encode()
    )
    return ProviderResult(body, 200, exchange_id=evidence.pk)


def sync_feed(transactions=None, ledger="1000.00", available=None, **kwargs):
    tx = provider_page(transactions if transactions is not None else [entry()])
    account = provider_page(
        [
            {
                "id": ACCOUNT,
                "currency": "ZMW",
                "ledgerBalance": ledger,
                "availableBalance": available or ledger,
            }
        ]
    )
    with patch("apps.payments.balances.Provider") as provider:
        provider.return_value.request.side_effect = [tx, account]
        return sync_balance()


def test_first_sync_is_a_baseline_then_independent_comparison_matches():
    baseline = sync_feed()
    assert baseline.status == "baseline"
    assert baseline.ledger_balance == Decimal("1000.00")
    assert ProviderAccount.objects.get().opening_balance == Decimal("900.00")
    comparison = sync_feed()
    assert comparison.status == "matched"
    assert comparison.difference == 0 and comparison.app_difference == 0
    assert ProviderTransaction.objects.count() == 1
    assert BalanceSnapshot.objects.count() == 2


def test_unknown_cash_movement_is_visible_without_changing_the_baseline():
    sync_feed()
    snapshot = sync_feed([entry(), entry("txn-2", "50")], ledger="1050")
    assert snapshot.status == "mismatch"
    assert snapshot.difference == 0
    assert snapshot.app_difference == Decimal("50")
    assert ProviderAccount.objects.get().opening_balance == Decimal("900")


def test_provider_balance_arithmetic_difference_is_retained():
    sync_feed()
    snapshot = sync_feed(ledger="999")
    assert snapshot.status == "mismatch" and snapshot.difference == Decimal("-1")


def test_changed_or_disappearing_provider_rows_are_not_overwritten():
    sync_feed()
    assert sync_feed([entry(amount="101")]).issue == "provider_transaction_changed"
    assert ProviderTransaction.objects.get().amount == Decimal("100")
    assert sync_feed([]).issue == "provider_transaction_history_incomplete"


@pytest.mark.parametrize("failure", ["http", "missing-pages", "wrong-account", "wrong-currency"])
def test_incomplete_import_never_establishes_a_baseline(failure):
    tx = provider_page([entry()])
    account = provider_page(
        [{"id": ACCOUNT, "currency": "ZMW", "ledgerBalance": "1000", "availableBalance": "1000"}]
    )
    if failure == "http":
        tx = ProviderResult({}, 503, "http_error")
    elif failure == "missing-pages":
        tx.payload["meta"] = {}
    elif failure == "wrong-account":
        tx.payload["data"][0]["accountId"] = "other"
    else:
        account.payload["data"][0]["currency"] = "USD"
    with patch("apps.payments.balances.Provider") as provider:
        provider.return_value.request.side_effect = [tx, account]
        snapshot = sync_balance()
    assert snapshot.status == "incomplete"
    assert ProviderAccount.objects.get().opening_balance is None


def test_feed_reads_all_pages_and_keeps_each_transaction_once():
    responses = [
        provider_page([entry()], count=2),
        provider_page([entry("txn-2", "10", "debit")], count=2),
        provider_page(
            [{"id": ACCOUNT, "currency": "ZMW", "ledgerBalance": "90", "availableBalance": "90"}]
        ),
    ]
    with patch("apps.payments.balances.Provider") as provider:
        provider.return_value.request.side_effect = responses
        result = sync_balance()
        assert [call.kwargs["page"] for call in provider.return_value.request.call_args_list] == [
            1,
            2,
            1,
        ]
    assert result.credits_total == Decimal("100")
    assert result.debits_total == Decimal("10")
    assert ProviderTransaction.objects.count() == 2


def test_imported_financial_records_are_immutable_on_postgres():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL immutability triggers")
    sync_feed()
    from django.db import DatabaseError

    with pytest.raises(DatabaseError), transaction.atomic():
        ProviderTransaction.objects.update(amount=1)
    with pytest.raises(DatabaseError), transaction.atomic():
        BalanceSnapshot.objects.all().delete()
