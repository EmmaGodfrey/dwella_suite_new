"""Compare Lenco's account with Dwella's records before any payout.

Each sync reads the balance, the transactions since a little before the newest
one already imported, then the balance again. Two independent checks follow:

* consistent: the opening balance plus every imported credit, minus every
  debit, equals Lenco's ledger balance. A gap or a changed row fails it and
  the next sync re-imports the full history.
* covered: the ledger holds at least the rent still owed to landlords
  (settled rent not yet paid out or in flight). Money above that, such as
  Dwella's own float, is shown as surplus and never blocks payouts.

Payouts need a fresh sync that is both. A balance record is written only when
the outcome changes; otherwise the account's check time moves forward.
"""

import hashlib
import json
from datetime import datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import (
    BalanceSnapshot,
    Collection,
    Payout,
    ProviderAccount,
    ProviderTransaction,
    Withdrawal,
)
from .provider import Provider

FRESH_FOR = timedelta(minutes=7)
# Lenco's date filter does not state a time zone; overlap generously.
OVERLAP = timedelta(days=2)
IN_FLIGHT = ("submitting", "pending")
ZERO = Decimal("0")


class BalanceSyncError(Exception):
    pass


def can_reserve_payout(row):
    """Call inside the payout claim transaction, before committing a debit intent."""
    collection = row.collection
    return can_reserve(collection.environment, collection.debit_account_id, row.amount, row)


def can_reserve(environment, account_id, needed, row):
    """Whether a fresh, matched Lenco balance covers `needed` after everything
    already committed. Call inside the claim transaction of `row`."""
    account = (
        ProviderAccount.objects.select_for_update()
        .filter(environment=environment, account_id=account_id)
        .first()
    )
    if account is None or account.checked_at is None:
        return False
    snapshot = BalanceSnapshot.objects.filter(account=account).first()
    if (
        snapshot is None
        or snapshot.status != "matched"
        or account.checked_at < timezone.now() - FRESH_FOR
        or snapshot.available_balance is None
    ):
        return False
    # Anything the balance read may not reflect yet is reserved.
    unsettled = Q(status__in=[*IN_FLIGHT, "review"]) | Q(
        status="successful", confirmed_at__gt=account.checked_at
    )
    payouts = Payout.objects.filter(
        collection__environment=environment, collection__debit_account_id=account_id
    )
    withdrawals = Withdrawal.objects.filter(environment=environment, debit_account_id=account_id)
    if isinstance(row, Payout):
        payouts = payouts.exclude(pk=row.pk)
    else:
        withdrawals = withdrawals.exclude(pk=row.pk)
    committed = payouts.filter(unsettled).aggregate(total=Sum("amount"), fees=Sum("fee"))
    sending = withdrawals.filter(unsettled).aggregate(total=Sum("amount"), fees=Sum("fee_reserved"))
    reserved = sum(
        (value or ZERO)
        for value in (committed["total"], committed["fees"], sending["total"], sending["fees"])
    )
    return snapshot.available_balance - reserved >= needed


def balance_amount(value):
    try:
        result = Decimal(str(value))
        if (
            not result.is_finite()
            or abs(result) > Decimal("9999999999999999.99")
            or result != result.quantize(Decimal("0.01"))
        ):
            raise ValueError
        return result
    except (InvalidOperation, ValueError, TypeError):
        raise BalanceSyncError("invalid_balance_amount") from None


def pages(provider, operation, **kwargs):
    """Every advertised page once; a row repeated by shifting pages is skipped."""
    expected_pages = None
    seen = {}
    for page in range(1, 101):
        result = provider.request(operation, page=page, **kwargs)
        payload = result.payload
        if (
            result.error
            or result.http_status != 200
            or payload.get("status") is not True
            or not isinstance(payload.get("data"), list)
        ):
            raise BalanceSyncError("provider_ledger_unavailable")
        meta = payload.get("meta") or {}
        count = meta.get("pageCount")
        if not isinstance(count, int) or isinstance(count, bool) or not 0 <= count <= 100:
            raise BalanceSyncError("pagination_incomplete")
        if expected_pages is not None and count != expected_pages:
            raise BalanceSyncError("ledger_changed_during_sync")
        expected_pages = count
        for item in payload["data"]:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("id"), str)
                or not 0 < len(item["id"]) <= 100
            ):
                raise BalanceSyncError("invalid_or_repeated_ledger_row")
            if item["id"] in seen:
                if seen[item["id"]] != item:
                    raise BalanceSyncError("invalid_or_repeated_ledger_row")
                continue
            seen[item["id"]] = item
            yield item, result.exchange_id
        if page >= max(count, 1):
            return
    raise BalanceSyncError("pagination_incomplete")


def read_balance(provider, account):
    rows = [
        item for item, _ in pages(provider, "accounts") if item["id"] == str(account.account_id)
    ]
    if len(rows) != 1 or rows[0].get("currency") != account.currency:
        raise BalanceSyncError("collection_account_not_found")
    return balance_amount(rows[0].get("availableBalance")), balance_amount(
        rows[0].get("ledgerBalance")
    )


def transaction_row(account, item, exchange_id):
    if item.get("accountId") != str(account.account_id) or item.get("type") not in {
        "credit",
        "debit",
    }:
        raise BalanceSyncError("transaction_account_or_type_mismatch")
    amount = balance_amount(item.get("amount"))
    posted = parse_datetime(item.get("datetime", ""))
    if amount < 0 or posted is None or posted.tzinfo is None:
        raise BalanceSyncError("invalid_provider_transaction")
    canonical = {key: item.get(key) for key in ("id", "accountId", "type", "amount", "datetime")}
    return ProviderTransaction(
        account=account,
        provider_id=item["id"],
        kind=item["type"],
        amount=amount,
        posted_at=posted,
        exchange_id=exchange_id,
        content_digest=hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest(),
    )


def landlord_totals(account):
    """Dwella's side in two aggregate queries, however many payments exist."""
    collections = Collection.objects.filter(
        environment=account.environment, debit_account_id=str(account.account_id)
    )
    rent = collections.aggregate(
        collected=Sum("amount", filter=Q(status="successful")),
        settled=Sum("settled_amount", filter=Q(settled=True)),
    )
    payouts = Payout.objects.filter(collection__in=collections).aggregate(
        paid=Sum("amount", filter=Q(status="successful")),
        fees=Sum("fee", filter=Q(status="successful")),
        in_flight=Sum("amount", filter=Q(status__in=IN_FLIGHT)),
    )
    withdrawals = Withdrawal.objects.filter(
        environment=account.environment, debit_account_id=str(account.account_id)
    ).aggregate(
        paid=Sum("amount", filter=Q(status="successful")),
        charged=Sum("fee_charged", filter=Q(status="successful")),
        fees=Sum("fee", filter=Q(status="successful")),
        in_flight=Sum("amount", filter=Q(status__in=IN_FLIGHT)),
        in_flight_fees=Sum("fee_reserved", filter=Q(status__in=IN_FLIGHT)),
    )
    settled = rent["settled"] or ZERO
    paid = (payouts["paid"] or ZERO) + (withdrawals["paid"] or ZERO)
    in_flight = sum(
        (value or ZERO)
        for value in (
            payouts["in_flight"],
            withdrawals["in_flight"],
            withdrawals["in_flight_fees"],
        )
    )
    return {
        "rent_collections_total": rent["collected"] or ZERO,
        "rent_settled_total": settled,
        "payouts_total": paid,
        "payout_fees_total": (payouts["fees"] or ZERO) + (withdrawals["fees"] or ZERO),
        # In-flight transfers may already be debited, so they are not counted as
        # held; one in review stays held until someone resolves it. Fees landlords
        # paid on withdrawals left their share of the balance too.
        "held_for_landlords": settled - paid - (withdrawals["charged"] or ZERO) - in_flight,
    }


def sync_balance():
    """Read-only provider requests; never fixes a discrepancy silently."""
    environment = settings.LENCO_ENVIRONMENT
    account, _ = ProviderAccount.objects.get_or_create(
        environment=environment,
        account_id=settings.LENCO_DEBIT_ACCOUNT_ID,
        defaults={"currency": "ZMW"},
    )
    since = None
    if account.opening_balance is not None and not account.full_scan_needed:
        newest = (
            ProviderTransaction.objects.filter(account=account)
            .order_by("-posted_at")
            .values_list("posted_at", flat=True)
            .first()
        )
        since = timezone.localdate(newest - OVERLAP) if newest else None
    full = since is None
    provider = Provider(environment)
    started = timezone.now()
    fetched, available, ledger, issue = {}, None, None, ""
    try:
        before = read_balance(provider, account)
        for item, exchange_id in pages(
            provider, "transactions", account_id=str(account.account_id), since=since
        ):
            fetched[item["id"]] = transaction_row(account, item, exchange_id)
        available, ledger = read_balance(provider, account)
        if before[1] != ledger:
            raise BalanceSyncError("ledger_moved_during_sync")
    except (BalanceSyncError, ValueError, TypeError) as exc:
        issue = str(exc) if isinstance(exc, BalanceSyncError) else "invalid_provider_ledger"
    with transaction.atomic():
        account = ProviderAccount.objects.select_for_update().get(pk=account.pk)
        credits = debits = None
        imported = 0
        if not issue:
            issue = _import(account, fetched, since)
        if not issue:
            totals = ProviderTransaction.objects.filter(account=account).aggregate(
                credits=Sum("amount", filter=Q(kind="credit")),
                debits=Sum("amount", filter=Q(kind="debit")),
                count=Count("id"),
            )
            credits, debits = totals["credits"] or ZERO, totals["debits"] or ZERO
            imported = totals["count"]
        app = landlord_totals(account)
        baseline = not issue and account.opening_balance is None
        if baseline:
            account.opening_balance = ledger - credits + debits
        expected = (
            account.opening_balance + credits - debits
            if not issue and account.opening_balance is not None
            else None
        )
        difference = ledger - expected if expected is not None else None
        surplus = ledger - app["held_for_landlords"] if ledger is not None else None
        if issue:
            status = "incomplete"
        elif baseline:
            status = "baseline"
        elif difference != 0:
            status = "mismatch"
        elif surplus < 0:
            status = "shortfall"
        else:
            status = "matched"
        # A gap in an incremental import shows up as a mismatch: re-import
        # everything once. A full import that still disagrees is a real
        # difference and stays visible without re-reading the history each time.
        if status == "mismatch" and not full:
            account.full_scan_needed = True
        elif full and status != "incomplete":
            account.full_scan_needed = False
        account.checked_at = started
        account.save()
        values = {
            "available_balance": available,
            "ledger_balance": ledger,
            "expected_balance": expected,
            "difference": difference,
            "surplus": surplus,
            "credits_total": credits or ZERO,
            "debits_total": debits or ZERO,
            "transaction_count": imported,
            "status": status,
            "issue": issue,
            **app,
        }
        latest = BalanceSnapshot.objects.filter(account=account).first()
        if latest and all(getattr(latest, key) == value for key, value in values.items()):
            return latest
        return BalanceSnapshot.objects.create(account=account, **values)


def _import(account, fetched, since):
    """Insert new rows in bulk; report changed or missing ones. Returns an issue."""
    known = dict(
        ProviderTransaction.objects.filter(
            account=account, provider_id__in=list(fetched)
        ).values_list("provider_id", "content_digest")
    )
    if any(known[key] != row.content_digest for key, row in fetched.items() if key in known):
        return "provider_transaction_changed"
    stored = ProviderTransaction.objects.filter(account=account)
    if since is not None:
        # Rows well inside the fetched window must all still be there.
        cutoff = datetime.combine(since + timedelta(days=1), time.min)
        stored = stored.filter(posted_at__gte=timezone.make_aware(cutoff))
    if stored.exclude(provider_id__in=list(fetched)).exists():
        return "provider_transaction_history_incomplete"
    ProviderTransaction.objects.bulk_create(
        [row for key, row in fetched.items() if key not in known]
    )
    return ""
