import hashlib
import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import BalanceSnapshot, Collection, Payout, ProviderAccount, ProviderTransaction
from .provider import Provider


class BalanceSyncError(Exception):
    pass


def can_reserve_payout(row):
    """Call inside the payout claim transaction, before committing a debit intent."""
    from datetime import timedelta

    collection = row.collection
    account = (
        ProviderAccount.objects.select_for_update()
        .filter(environment=collection.environment, account_id=collection.debit_account_id)
        .first()
    )
    if account is None:
        return False
    snapshot = BalanceSnapshot.objects.filter(account=account).first()
    if (
        snapshot is None
        or snapshot.status != "matched"
        or snapshot.created_at < timezone.now() - timedelta(minutes=6)
        or snapshot.available_balance is None
    ):
        return False
    committed = (
        Payout.objects.filter(
            collection__environment=collection.environment,
            collection__debit_account_id=collection.debit_account_id,
        )
        .exclude(pk=row.pk)
        .filter(
            Q(status__in=["submitting", "pending", "review"])
            | Q(status="successful", confirmed_at__gt=snapshot.created_at)
        )
        .aggregate(total=Sum("amount"), fees=Sum("fee"))
    )
    reserved = (committed["total"] or Decimal("0")) + (committed["fees"] or Decimal("0"))
    return snapshot.available_balance - reserved >= row.amount


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
    """Import every advertised page, or explicitly mark the comparison incomplete."""
    expected_pages = None
    seen_ids = set()
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
                or item["id"] in seen_ids
            ):
                raise BalanceSyncError("invalid_or_repeated_ledger_row")
            seen_ids.add(item["id"])
            yield item, result.exchange_id
        if page >= max(count, 1):
            return
    raise BalanceSyncError("pagination_incomplete")


def application_totals(account):
    rows = Collection.objects.filter(
        environment=account.environment, debit_account_id=str(account.account_id)
    )
    successful = rows.filter(status="successful")
    rent = successful.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    # Settled receipts needing manual allocation still represent real money.
    settled = rows.filter(settled=True).aggregate(total=Sum("settled_amount"))["total"] or Decimal(
        "0"
    )
    paid = Payout.objects.filter(collection__in=rows, status="successful")
    totals = paid.aggregate(principal=Sum("amount"), fees=Sum("fee"))
    return {
        "rent_collections_total": rent,
        "rent_settled_total": settled,
        "payouts_total": totals["principal"] or Decimal("0"),
        "payout_fees_total": totals["fees"] or Decimal("0"),
    }


def sync_balance():
    """Read-only provider requests; persist snapshots, never fix discrepancies silently."""
    environment = settings.LENCO_ENVIRONMENT
    account_id = settings.LENCO_DEBIT_ACCOUNT_ID
    account, _ = ProviderAccount.objects.get_or_create(
        environment=environment, account_id=account_id, defaults={"currency": "ZMW"}
    )
    provider = Provider(environment)
    credits = debits = Decimal("0")
    imported = []
    available = ledger = None
    issue = ""
    try:
        # Read transaction pages first, balances last. An in-flight provider
        # transaction can produce a temporary difference; a later sync resolves
        # it without changing the frozen opening balance.
        for item, exchange_id in pages(provider, "transactions", account_id=account_id):
            if item.get("accountId") != str(account.account_id) or item.get("type") not in {
                "credit",
                "debit",
            }:
                raise BalanceSyncError("transaction_account_or_type_mismatch")
            amount = balance_amount(item.get("amount"))
            posted = parse_datetime(item.get("datetime", ""))
            if amount < 0 or posted is None or posted.tzinfo is None:
                raise BalanceSyncError("invalid_provider_transaction")
            canonical = {
                key: item.get(key) for key in ("id", "accountId", "type", "amount", "datetime")
            }
            imported.append(
                {
                    "provider_id": item["id"],
                    "kind": item["type"],
                    "amount": amount,
                    "posted_at": posted,
                    "exchange_id": exchange_id,
                    "content_digest": hashlib.sha256(
                        json.dumps(canonical, sort_keys=True).encode()
                    ).hexdigest(),
                }
            )
        accounts = [
            item for item, _ in pages(provider, "accounts") if item["id"] == str(account.account_id)
        ]
        if len(accounts) != 1 or accounts[0].get("currency") != account.currency:
            raise BalanceSyncError("collection_account_not_found")
        available = balance_amount(accounts[0].get("availableBalance"))
        ledger = balance_amount(accounts[0].get("ledgerBalance"))
    except (BalanceSyncError, ValueError, TypeError) as exc:
        issue = str(exc) if isinstance(exc, BalanceSyncError) else "invalid_provider_ledger"
    with transaction.atomic():
        account = ProviderAccount.objects.select_for_update().get(pk=account.pk)
        if not issue:
            for item in imported:
                existing, created = ProviderTransaction.objects.get_or_create(
                    account=account, provider_id=item["provider_id"], defaults=item
                )
                if not created and existing.content_digest != item["content_digest"]:
                    issue = "provider_transaction_changed"
            totals = (
                ProviderTransaction.objects.filter(account=account)
                .values("kind")
                .annotate(total=Sum("amount"))
            )
            by_kind = {row["kind"]: row["total"] for row in totals}
            credits, debits = (
                by_kind.get("credit", Decimal("0")),
                by_kind.get("debit", Decimal("0")),
            )
            if len(imported) != ProviderTransaction.objects.filter(account=account).count():
                issue = issue or "provider_transaction_history_incomplete"
        app = application_totals(account)
        app_net = app["rent_settled_total"] - app["payouts_total"] - app["payout_fees_total"]
        baseline = account.opening_balance is None
        if not issue and baseline:
            account.opening_balance = ledger - credits + debits
            account.app_opening_balance = ledger - app_net
            account.save()
        expected = (
            account.opening_balance + credits - debits
            if account.opening_balance is not None and not issue
            else None
        )
        app_expected = (
            account.app_opening_balance + app_net
            if account.app_opening_balance is not None and not issue
            else None
        )
        difference = ledger - expected if expected is not None else None
        app_difference = ledger - app_expected if app_expected is not None else None
        status = (
            "incomplete"
            if issue
            else "baseline"
            if baseline
            else "matched"
            if difference == 0 and app_difference == 0
            else "mismatch"
        )
        return BalanceSnapshot.objects.create(
            account=account,
            available_balance=available,
            ledger_balance=ledger,
            expected_balance=expected,
            difference=difference,
            app_expected_balance=app_expected,
            app_difference=app_difference,
            credits_total=credits,
            debits_total=debits,
            transaction_count=len(imported),
            status=status,
            issue=issue,
            **app,
        )
