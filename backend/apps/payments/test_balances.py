import json
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.db import connection, transaction

from .balances import sync_balance
from .evidence import record_exchange
from .models import BalanceSnapshot, ProviderAccount, ProviderTransaction
from .provider import ProviderResult
from .testing import ACCOUNT, paid

pytestmark = pytest.mark.django_db


def entry(identifier="txn-1", amount="100.00", kind="credit", when="2026-10-25T10:00:00Z"):
    return {
        "id": identifier,
        "amount": amount,
        "type": kind,
        "accountId": ACCOUNT,
        "datetime": when,
    }


def provider_page(data, *, count=1):
    body = {"status": True, "data": data, "meta": {"pageCount": count}}
    evidence = record_exchange(
        environment="sandbox", operation="test_feed", body=json.dumps(body).encode()
    )
    return ProviderResult(body, 200, exchange_id=evidence.pk)


def balance_page(ledger, available=None):
    return provider_page(
        [
            {
                "id": ACCOUNT,
                "currency": "ZMW",
                "ledgerBalance": ledger,
                "availableBalance": available or ledger,
            }
        ]
    )


def run_sync(responses):
    with patch("apps.payments.balances.Provider") as provider:
        provider.return_value.request.side_effect = responses
        snapshot = sync_balance()
    return snapshot, provider.return_value.request.call_args_list


def sync_feed(transactions=None, ledger="1000.00", available=None, after=None):
    tx = provider_page(transactions if transactions is not None else [entry()])
    first = balance_page(ledger, available)
    last = balance_page(after or ledger, available)
    return run_sync([first, tx, last])[0]


def test_first_sync_is_a_baseline_then_independent_comparison_matches():
    baseline = sync_feed()
    assert baseline.status == "baseline"
    assert baseline.ledger_balance == Decimal("1000.00")
    assert ProviderAccount.objects.get().opening_balance == Decimal("900.00")
    comparison = sync_feed()
    assert comparison.status == "matched"
    assert comparison.difference == 0 and comparison.surplus == Decimal("1000")
    assert ProviderTransaction.objects.count() == 1
    assert BalanceSnapshot.objects.count() == 2


def test_an_unchanged_sync_writes_no_new_balance_record():
    sync_feed()
    sync_feed()
    checked = ProviderAccount.objects.get().checked_at
    again = sync_feed()
    assert BalanceSnapshot.objects.count() == 2 and again.status == "matched"
    assert ProviderAccount.objects.get().checked_at > checked


def test_later_syncs_only_ask_for_recent_transactions():
    sync_feed()
    _, calls = run_sync([balance_page("1000"), provider_page([entry()]), balance_page("1000")])
    transactions = [call for call in calls if call.args[0] == "transactions"]
    assert transactions[0].kwargs["since"] == date(2026, 10, 23)


def test_money_beyond_dwella_records_is_surplus_and_never_blocks():
    sync_feed()
    snapshot = sync_feed([entry(), entry("txn-2", "50")], ledger="1050")
    assert snapshot.status == "matched"
    assert snapshot.difference == 0 and snapshot.surplus == Decimal("1050")
    assert ProviderAccount.objects.get().opening_balance == Decimal("900")


def test_provider_balance_arithmetic_difference_triggers_one_full_reimport():
    sync_feed()
    snapshot = sync_feed(ledger="999")
    assert snapshot.status == "mismatch" and snapshot.difference == Decimal("-1")
    assert ProviderAccount.objects.get().full_scan_needed
    _, calls = run_sync([balance_page("999"), provider_page([entry()]), balance_page("999")])
    assert [call.kwargs.get("since") for call in calls if call.args[0] == "transactions"] == [None]
    # A full import that still disagrees stays visible but is not repeated.
    assert not ProviderAccount.objects.get().full_scan_needed


def test_a_balance_that_moves_during_the_sync_is_retried_not_reported():
    sync_feed()
    snapshot = sync_feed(after="1100")
    assert snapshot.status == "incomplete" and snapshot.issue == "ledger_moved_during_sync"


def test_rent_owed_to_landlords_must_be_covered(home):
    paid(home)  # 97.50 settled and waiting for its payout
    ProviderAccount.objects.filter(account_id=ACCOUNT).update(opening_balance=-50)
    snapshot = sync_feed(ledger="50.00")
    assert snapshot.difference == 0
    assert snapshot.held_for_landlords == Decimal("97.50")
    assert snapshot.status == "shortfall" and snapshot.surplus == Decimal("-47.50")


def test_changed_or_disappearing_provider_rows_are_not_overwritten():
    sync_feed()
    assert sync_feed([entry(amount="101")]).issue == "provider_transaction_changed"
    assert ProviderTransaction.objects.get().amount == Decimal("100")
    assert sync_feed([]).issue == "provider_transaction_history_incomplete"


@pytest.mark.parametrize("failure", ["http", "missing-pages", "wrong-account", "wrong-currency"])
def test_incomplete_import_never_establishes_a_baseline(failure):
    tx = provider_page([entry()])
    first, last = balance_page("1000"), balance_page("1000")
    if failure == "http":
        tx = ProviderResult({}, 503, "http_error")
    elif failure == "missing-pages":
        tx.payload["meta"] = {}
    elif failure == "wrong-account":
        tx.payload["data"][0]["accountId"] = "other"
    else:
        first.payload["data"][0]["currency"] = "USD"
    snapshot, _ = run_sync([first, tx, last])
    assert snapshot.status == "incomplete"
    assert ProviderAccount.objects.get().opening_balance is None


def test_feed_reads_all_pages_and_keeps_each_transaction_once():
    shifted = entry()  # a new row pushed this one onto the next page as well
    responses = [
        balance_page("90"),
        provider_page([entry()], count=2),
        provider_page([shifted, entry("txn-2", "10", "debit")], count=2),
        balance_page("90"),
    ]
    result, calls = run_sync(responses)
    assert [call.kwargs["page"] for call in calls] == [1, 1, 2, 1]
    assert result.credits_total == Decimal("100")
    assert result.debits_total == Decimal("10")
    assert ProviderTransaction.objects.count() == 2


def test_a_repeated_row_with_different_content_is_rejected():
    responses = [
        balance_page("90"),
        provider_page([entry()], count=2),
        provider_page([entry(amount="5")], count=2),
        balance_page("90"),
    ]
    snapshot, _ = run_sync(responses)
    assert snapshot.issue == "invalid_or_repeated_ledger_row"


def test_imported_financial_records_are_immutable_on_postgres():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL immutability triggers")
    sync_feed()
    from django.db import DatabaseError

    with pytest.raises(DatabaseError), transaction.atomic():
        ProviderTransaction.objects.update(amount=1)
    with pytest.raises(DatabaseError), transaction.atomic():
        BalanceSnapshot.objects.all().delete()
