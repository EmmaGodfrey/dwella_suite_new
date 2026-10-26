"""Landlord withdrawals of settled rent, and receiving-account checks.

A workspace's balance is its settled rent, less what legacy automatic payouts
took and what withdrawals have taken or are holding. A withdrawal reserves the
amount plus the highest Lenco fee for that amount under the workspace lock,
then the worker sends it once. An unknown outcome is asked about by the same
reference and never sent again.
"""

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.integrations.lenco import LencoError

from .models import Collection, Destination, Payout, Withdrawal
from .provider import Provider
from .schedule import PAYOUT_CONFIRMATION_LIMIT, payout_next_check
from .services import money, normalize_phone

ZERO = Decimal("0.00")
CENT = Decimal("0.01")
# Statuses whose money has left, or may have left, the workspace balance.
HOLDING = ("queued", "submitting", "pending", "review")
LEGACY_TAKEN = ("queued", "submitting", "pending", "successful", "review")
BANKS_KEY = "payments:lenco-banks"


def fee_bands(kind):
    return [(Decimal(top), Decimal(fee)) for top, fee in settings.LENCO_WITHDRAWAL_FEES[kind]]


def fee_for(kind, amount):
    """The fee reserved for sending this amount, or None above the largest band."""
    for top, fee in fee_bands(kind):
        if amount <= top:
            return fee
    return None


def largest_withdrawal(kind, available):
    """The most a landlord can receive so that it plus its fee fits the balance."""
    best, bottom = None, ZERO
    for top, fee in fee_bands(kind):
        candidate = min(top, available - fee)
        if candidate > bottom:
            best = candidate
        bottom = top
    minimum = Decimal(settings.LENCO_WITHDRAWAL_MINIMUM)
    return best if best is not None and best >= minimum else None


def balance(organization):
    """Settled, awaiting, processing and withdrawn totals for one workspace."""
    scope = {
        "organization": organization,
        "environment": settings.LENCO_ENVIRONMENT,
        "debit_account_id": settings.LENCO_DEBIT_ACCOUNT_ID,
    }
    rent = Collection.objects.filter(**scope, status="successful").aggregate(
        settled_total=Sum("settled_amount", filter=Q(settled=True)),
        awaiting_total=Sum("amount", filter=Q(settled=False)),
    )
    legacy = Payout.objects.filter(
        collection__organization=organization,
        collection__environment=scope["environment"],
        collection__debit_account_id=scope["debit_account_id"],
        status__in=LEGACY_TAKEN,
    ).aggregate(total=Sum("amount"))
    month = timezone.localdate().replace(day=1)
    taken = Withdrawal.objects.filter(**scope).aggregate(
        held=Sum("amount", filter=Q(status__in=HOLDING)),
        held_fees=Sum("fee_reserved", filter=Q(status__in=HOLDING)),
        sent=Sum("amount", filter=Q(status="successful")),
        sent_fees=Sum("fee_charged", filter=Q(status="successful")),
        month=Sum("amount", filter=Q(status="successful", confirmed_at__date__gte=month)),
        month_fees=Sum("fee_charged", filter=Q(status="successful", confirmed_at__date__gte=month)),
    )
    value = {key: amount or ZERO for key, amount in taken.items()}
    processing = value["held"] + value["held_fees"]
    available = (
        (rent["settled_total"] or ZERO)
        - (legacy["total"] or ZERO)
        - processing
        - value["sent"]
        - value["sent_fees"]
    )
    return {
        "available": available,
        "awaiting_settlement": rent["awaiting_total"] or ZERO,
        "processing": processing,
        "withdrawn_this_month": value["month"],
        "fees_this_month": value["month_fees"],
    }


def withdrawals_enabled():
    return bool(
        settings.LENCO_PAYOUTS_ENABLED
        and settings.LENCO_SECRET_KEY
        and settings.LENCO_DEBIT_ACCOUNT_ID
        and settings.LENCO_ENVIRONMENT in {"live", "sandbox"}
    )


def current_destination(organization):
    return Destination.objects.filter(organization=organization, enabled=True).first()


def quote(organization, amount):
    """The preview a landlord confirms: what they receive, the fee and the total."""
    destination = current_destination(organization)
    if destination is None:
        raise ValidationError("Add a receiving account before withdrawing.")
    amount = money(amount, positive=True)
    available = balance(organization)["available"]
    minimum = Decimal(settings.LENCO_WITHDRAWAL_MINIMUM)
    fee = fee_for(destination.kind, amount)
    if amount < minimum:
        raise ValidationError({"amount": f"The smallest withdrawal is K{minimum:,.2f}."})
    if fee is None:
        top = fee_bands(destination.kind)[-1][0]
        raise ValidationError({"amount": f"Withdraw at most K{top:,.2f} at a time."})
    if amount + fee > available:
        raise ValidationError({"amount": "This amount and its fee are more than your balance."})
    return destination, amount, fee, available


def request_withdrawal(*, organization, user, amount, fee, idempotency_key):
    """Reserve and queue one withdrawal; the same key returns the same withdrawal."""
    from apps.organizations.models import Organization

    if not withdrawals_enabled():
        raise ValidationError("Withdrawals are not enabled yet.")
    amount = money(amount, positive=True)
    # One workspace lock serialises withdrawals so two cannot spend one balance.
    with transaction.atomic():
        organization = Organization.objects.select_for_update().get(pk=organization.pk)
        existing = Withdrawal.objects.filter(
            organization=organization, requested_by=user, idempotency_key=idempotency_key
        ).first()
        if existing:
            if existing.amount != amount:
                raise ValidationError("This request was already used for a different amount.")
            return existing
        if not organization.is_active or organization.currency != "ZMW":
            raise ValidationError("Withdrawals need an active ZMW workspace.")
        destination, amount, reserved, _ = quote(organization, amount)
        if money(fee) != reserved:
            raise ValidationError(
                {"fee": "The transfer fee has changed. Review the new total before confirming."}
            )
        try:
            with transaction.atomic():
                return Withdrawal.objects.create(
                    organization=organization,
                    destination=destination,
                    requested_by=user,
                    environment=settings.LENCO_ENVIRONMENT,
                    debit_account_id=settings.LENCO_DEBIT_ACCOUNT_ID,
                    idempotency_key=idempotency_key,
                    amount=amount,
                    fee_reserved=reserved,
                    next_check_at=timezone.now(),
                )
        except IntegrityError:
            raise ValidationError("This request is already in use.") from None


def cancel_withdrawal(withdrawal):
    """Only a withdrawal that has not been claimed for sending can be cancelled."""
    with transaction.atomic():
        row = Withdrawal.objects.select_for_update().get(pk=withdrawal.pk)
        if row.status != Withdrawal.Status.QUEUED:
            raise ValidationError("This withdrawal is already being sent.")
        row.status, row.issue, row.next_check_at = Withdrawal.Status.CANCELLED, "", None
        row.save(update_fields=["status", "issue", "next_check_at", "updated_at"])
    return row


def _still_allowed(row):
    from apps.organizations.models import OrganizationMembership

    return (
        row.organization.is_active
        and row.destination.enabled
        and row.debit_account_id == settings.LENCO_DEBIT_ACCOUNT_ID
        and OrganizationMembership.objects.filter(
            organization=row.organization,
            user=row.requested_by,
            user__is_active=True,
            is_active=True,
            role="landlord",
        ).exists()
    )


def _payload(row):
    destination = row.destination
    payload = {
        "accountId": row.debit_account_id,
        "amount": float(row.amount),
        "reference": row.reference,
        "narration": "Dwella rent withdrawal",
        "country": "zm",
    }
    if destination.kind == Destination.Kind.BANK_ACCOUNT:
        payload |= {"accountNumber": destination.account_number, "bankId": destination.bank_id}
    else:
        payload |= {"phone": destination.phone, "operator": destination.operator}
    return payload


def process_withdrawal(withdrawal):
    """Send a queued withdrawal once, or ask Lenco about a sent one."""
    # The claim commits BEFORE the request. A crash or timeout leads to a status
    # check of the same reference, never to a second transfer.
    with transaction.atomic():
        row = (
            Withdrawal.objects.select_for_update(of=("self",))
            .select_related("destination", "organization")
            .get(pk=withdrawal.pk)
        )
        now = timezone.now()
        if row.status not in HOLDING or row.status == Withdrawal.Status.REVIEW:
            if row.next_check_at:
                row.next_check_at = None
                row.save(update_fields=["next_check_at", "updated_at"])
            return
        submit = row.status == Withdrawal.Status.QUEUED
        if submit:
            if not settings.LENCO_PAYOUTS_ENABLED:
                row.next_check_at = now + timedelta(minutes=15)
                row.save(update_fields=["next_check_at", "updated_at"])
                return
            if not _still_allowed(row):
                # Nothing was sent; the reserve returns to the balance.
                row.status, row.issue = Withdrawal.Status.CANCELLED, "withdrawal_no_longer_allowed"
                row.next_check_at = None
                row.save()
                return
            from .balances import can_reserve

            if not can_reserve(
                row.environment, row.debit_account_id, row.amount + row.fee_reserved, row
            ):
                row.issue = "awaiting_balance_reconciliation"
                row.next_check_at = now + timedelta(minutes=1)
                row.save()
                return
            row.status, row.issue = Withdrawal.Status.SUBMITTING, ""
            row.submitted_at = row.last_checked_at = now
            row.next_check_at = payout_next_check(row, now)
            row.save()
        elif now - (row.submitted_at or row.created_at) > PAYOUT_CONFIRMATION_LIMIT:
            row.status, row.issue = Withdrawal.Status.REVIEW, "withdrawal_unconfirmed"
            row.next_check_at = None
            row.save()
            return
    provider = Provider(row.environment)
    if submit:
        result = provider.request("withdrawal_submit", withdrawal=row, payload=_payload(row))
    else:
        result = provider.request("withdrawal_status", withdrawal=row)
    _apply_withdrawal_result(row, result, submitted=submit)


def _refused(result):
    """Lenco answered the transfer request itself with a refusal: nothing was sent."""
    body = result.payload if isinstance(result.payload, dict) else {}
    message = str(body.get("message", "")).lower()
    return (
        result.http_status in {400, 401, 403, 422}
        and body.get("status") is False
        and "duplicate" not in message
    )


def _apply_withdrawal_result(withdrawal, result, submitted=False):
    with transaction.atomic():
        row = (
            Withdrawal.objects.select_for_update(of=("self",))
            .select_related("destination")
            .get(pk=withdrawal.pk)
        )
        now = timezone.now()
        row.last_checked_at = now
        if submitted and row.status == Withdrawal.Status.SUBMITTING and _refused(result):
            row.status, row.issue = Withdrawal.Status.FAILED, "withdrawal_refused"
        else:
            _apply_withdrawal_data(row, result, now)
        row.next_check_at = payout_next_check(row, now)
        row.save()


def _matches_destination(destination, recipient):
    if not isinstance(recipient, dict) or recipient.get("type") != destination.kind:
        return False
    if destination.kind == Destination.Kind.BANK_ACCOUNT:
        bank = recipient.get("bank") or {}
        return (
            recipient.get("accountNumber") == destination.account_number
            and isinstance(bank, dict)
            and bank.get("id") == destination.bank_id
        )
    return (
        normalize_phone(recipient.get("phone", "")) == destination.phone
        and recipient.get("operator") == destination.operator
    )


def _apply_withdrawal_data(row, result, now):
    if row.status in {Withdrawal.Status.SUCCESSFUL, Withdrawal.Status.CANCELLED}:
        return
    payload = result.payload if isinstance(result.payload, dict) else {}
    data = payload.get("data")
    if (
        result.error
        or result.http_status != 200
        or payload.get("status") is not True
        or not isinstance(data, dict)
    ):
        row.issue = result.error or "withdrawal_not_confirmed"
        return
    state = data.get("status")
    try:
        identity = (
            data.get("reference") == row.reference
            and data.get("accountId") == row.debit_account_id
            and money(data.get("amount"), positive=True) == row.amount
            and isinstance(data.get("id"), str)
            and 0 < len(data["id"]) <= 100
        )
        details = (
            identity
            and data.get("currency") == "ZMW"
            and _matches_destination(row.destination, data.get("creditAccount"))
        )
    except (ValidationError, AttributeError):
        identity = details = False
    # Lenco omits some details on a refused transfer. Our reference, account and
    # amount still identify it, and a refusal moves no money.
    if not (details or (identity and state == "failed")):
        row.status, row.issue = Withdrawal.Status.REVIEW, "withdrawal_details_mismatch"
        return
    if row.provider_id and row.provider_id != data["id"]:
        row.status, row.issue = Withdrawal.Status.REVIEW, "withdrawal_identity_changed"
        return
    row.provider_id = data["id"]
    if state not in {"pending", "successful", "failed"}:
        return
    row.status = state
    row.issue = ""
    if state == Withdrawal.Status.FAILED:
        row.issue = "withdrawal_failed"
        return
    try:
        row.fee = money(data["fee"]) if data.get("fee") is not None else None
    except ValidationError:
        row.fee, row.issue = None, "invalid_withdrawal_fee"
    if state == Withdrawal.Status.SUCCESSFUL:
        row.confirmed_at = row.confirmed_at or now
        # The landlord never pays more than the fee they confirmed. A higher or
        # missing fee is absorbed and left visible for reconciliation.
        if row.fee is None:
            row.fee_charged = row.fee_reserved
            row.issue = row.issue or "withdrawal_fee_not_reported"
        else:
            row.fee_charged = min(row.fee, row.fee_reserved)
            if row.fee > row.fee_reserved:
                row.issue = "withdrawal_fee_above_reserve"


def _ask_lenco(operation, **kwargs):
    # A missing or malformed key means Lenco could not be asked, not a crash.
    try:
        return Provider(settings.LENCO_ENVIRONMENT).request(operation, **kwargs)
    except LencoError as exc:
        raise ValidationError("Lenco is not configured for this environment.") from exc


def banks():
    """Zambian banks from Lenco, kept for a day."""
    cached = cache.get(BANKS_KEY)
    if cached is not None:
        return cached
    result = _ask_lenco("banks")
    data = result.payload.get("data") if isinstance(result.payload, dict) else None
    if result.error or result.http_status != 200 or not isinstance(data, list):
        raise ValidationError("Could not load banks from Lenco. Try again shortly.")
    rows = sorted(
        (
            {"id": item["id"], "name": item["name"]}
            for item in data
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and isinstance(item.get("name"), str)
            and 0 < len(item["id"]) <= 64
            and 0 < len(item["name"]) <= 180
        ),
        key=lambda item: item["name"].lower(),
    )
    cache.set(BANKS_KEY, rows, timeout=24 * 60 * 60)
    return rows


class AccountNotFound(ValidationError):
    pass


def look_up_account(details):
    """Ask Lenco for the registered name of a receiving account.

    Returns the name. Raises AccountNotFound when Lenco says the account does
    not exist, and ValidationError when Lenco could not be asked.
    """
    if details["kind"] == Destination.Kind.BANK_ACCOUNT:
        operation = "resolve_bank_account"
        payload = {
            "accountNumber": details["account_number"],
            "bankId": details["bank_id"],
            "country": "zm",
        }
    else:
        operation = "resolve_mobile_money"
        payload = {
            "phone": "0" + details["phone"].removeprefix("+260"),
            "operator": details["operator"],
            "country": "zm",
        }
    result = _ask_lenco(operation, payload=payload)
    body = result.payload if isinstance(result.payload, dict) else {}
    data = body.get("data")
    if result.http_status in {400, 404} and body.get("status") is False:
        raise AccountNotFound("Lenco could not find this account. Check the details and try again.")
    if result.error or result.http_status != 200 or not isinstance(data, dict):
        raise ValidationError("Could not check this account with Lenco. Try again shortly.")
    name = data.get("accountName")
    if not isinstance(name, str) or not 0 < len(name.strip()) <= 180:
        raise ValidationError("Lenco did not return a name for this account.")
    return name.strip()
