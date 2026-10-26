from datetime import timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.billing.models import Invoice, Payment
from apps.billing.services import record_payment
from apps.subscriptions.catalog import Feature
from apps.subscriptions.services import require_feature

from .models import Collection, Destination, Payout
from .provider import Provider
from .schedule import (
    CHECKOUT_WINDOW,
    PAYOUT_CONFIRMATION_LIMIT,
    SETTLEMENT_OVERDUE,
    checkout_started,
    checkout_window_over,
    collection_next_check,
    parse_stamp,
    payout_next_check,
    stamp,
)


def money(value, *, positive=False):
    try:
        amount = Decimal(str(value))
        if (
            not amount.is_finite()
            or amount < 0
            or amount > Decimal("9999999999.99")
            or amount != amount.quantize(Decimal("0.01"))
            or (positive and amount == 0)
        ):
            raise ValueError
        return amount
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError("Invalid payment amount.") from None


@transaction.atomic
def approve_destination(
    *,
    organization,
    user,
    account_name,
    reason,
    kind="mobile-money",
    phone="",
    operator="",
    bank_id="",
    bank_name="",
    account_number="",
    lookup_name="",
):
    from apps.organizations.models import Organization

    Organization.objects.select_for_update().get(pk=organization.pk)
    details = {
        "kind": kind,
        "phone": phone,
        "operator": operator,
        "bank_id": bank_id,
        "bank_name": bank_name,
        "account_number": account_number,
        "account_name": account_name,
        "lookup_name": lookup_name,
    }
    current = Destination.objects.filter(organization=organization, enabled=True).first()
    if current and all(getattr(current, key) == value for key, value in details.items()):
        return current  # A repeated approval is not a new version.
    Destination.objects.filter(organization=organization, enabled=True).update(enabled=False)
    return Destination.objects.create(
        organization=organization, approved_by=user, approval_reason=reason, **details
    )


@transaction.atomic
def start_checkout(
    *, invoice, user, idempotency_key, amount, channel="checkout", phone="", operator=""
):
    if channel not in {"checkout", "card", "mobile-money"}:
        raise ValidationError("Choose a supported payment method.")
    if channel == "mobile-money":
        phone = normalize_phone(phone)
        if operator not in {"mtn", "airtel", "zamtel"}:
            raise ValidationError("Choose a supported mobile-money network.")
    elif phone or operator:
        raise ValidationError("Mobile-money details require the mobile-money payment method.")
    if not settings.LENCO_PAYMENTS_ENABLED:
        raise ValidationError("Online payments are not enabled yet.")
    require_feature(invoice.organization, Feature.ONLINE_PAYMENTS)
    if settings.LENCO_ENVIRONMENT not in {"live", "sandbox"} or not settings.LENCO_PUBLIC_KEY:
        raise ValidationError("Online payment configuration is incomplete.")
    try:
        UUID(settings.LENCO_DEBIT_ACCOUNT_ID)
    except (ValueError, TypeError):
        raise ValidationError("The collection account is not configured.") from None
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    amount = money(amount, positive=True)
    existing = Collection.objects.filter(
        organization=invoice.organization, initiated_by=user, idempotency_key=idempotency_key
    ).first()
    if existing:
        if (
            existing.invoice_id != invoice.pk
            or existing.amount != amount
            or existing.environment != settings.LENCO_ENVIRONMENT
            or (existing.channel, existing.payer_phone, existing.payer_operator)
            != (channel, phone, operator)
        ):
            raise ValidationError("This payment key was already used for different details.")
        return existing
    if not invoice.is_active or invoice.status not in Invoice.UNPAID_STATUSES:
        raise ValidationError("This invoice cannot accept online payments.")
    pending = Collection.objects.filter(invoice=invoice, status="pending").first()
    if pending:
        if (
            pending.initiated_by_id == user.pk
            and pending.amount == amount
            and pending.environment == settings.LENCO_ENVIRONMENT
            and amount <= invoice.balance
            and (
                (pending.channel, pending.payer_phone, pending.payer_operator)
                == (channel, phone, operator)
                or (pending.channel == "checkout" and channel == "card")
            )
        ):
            return pending
        until = timezone.localtime(checkout_started(pending) + CHECKOUT_WINDOW)
        raise ValidationError(
            f"A payment for this invoice is still open until {until:%H:%M}. "
            "Finish it in Lenco, or start a new one after that."
        )
    if amount > invoice.balance or invoice.organization.currency != "ZMW":
        raise ValidationError("Check the outstanding amount and invoice currency.")
    if not user.email:
        raise ValidationError("Your account needs an email address for checkout.")
    destination = Destination.objects.filter(
        organization=invoice.organization, enabled=True
    ).first()
    if destination is None:
        raise ValidationError("The manager's receiving number has not been set up yet.")
    try:
        with transaction.atomic():
            return Collection.objects.create(
                organization=invoice.organization,
                invoice=invoice,
                initiated_by=user,
                destination=destination,
                environment=settings.LENCO_ENVIRONMENT,
                idempotency_key=idempotency_key,
                amount=amount,
                channel=channel,
                payer_phone=phone,
                payer_operator=operator,
                currency="ZMW",
                debit_account_id=settings.LENCO_DEBIT_ACCOUNT_ID,
                next_check_at=timezone.now() + timedelta(seconds=30),
            )
    except IntegrityError:
        raise ValidationError(
            "This payment key is already in use. Check the original payment."
        ) from None


def checkout_payload(collection):
    return {
        "key": settings.LENCO_PUBLIC_KEY,
        "script_url": "https://pay.lenco.co/js/v1/inline.js"
        if collection.environment == "live"
        else "https://pay.sandbox.lenco.co/js/v1/inline.js",
        "reference": collection.reference,
        "amount": f"{collection.amount:.2f}",
        "currency": collection.currency,
        "email": collection.initiated_by.email,
        "channels": ["card"] if collection.channel == "card" else ["mobile-money", "card"],
        "bearer": "merchant",
    }


def _valid_data(result):
    return (
        not result.error
        and result.http_status == 200
        and result.payload.get("status") is True
        and isinstance(result.payload.get("data"), dict)
    )


def _issue(collection, code):
    collection.issue = code
    if collection.status != Collection.Status.SUCCESSFUL:
        collection.status = Collection.Status.REVIEW


def reconcile_collection(collection):
    """Ask Lenco about one checkout and apply the answer. Safe to repeat."""
    result = Provider(collection.environment).request("collection_status", collection=collection)
    _apply_verified_collection(collection, result)


def submit_mobile_money(collection):
    """Claim once before sending; unknown outcomes are queried, never resubmitted."""
    with transaction.atomic():
        row = Collection.objects.select_for_update().get(pk=collection.pk)
        if (
            row.channel != "mobile-money"
            or row.status != Collection.Status.PENDING
            or row.collection_submitted_at is not None
        ):
            return row
        row.collection_submitted_at = timezone.now()
        row.next_check_at = row.collection_submitted_at + timedelta(seconds=30)
        row.save(update_fields=["collection_submitted_at", "next_check_at", "updated_at"])
    # No invoice/collection locks are held during this potentially slow call.
    result = Provider(row.environment).request(
        "collection_submit",
        collection=row,
        payload={
            "amount": float(row.amount),
            "reference": row.reference,
            "phone": row.payer_phone,
            "operator": row.payer_operator,
            "country": "zm",
            "bearer": "merchant",
        },
    )
    _apply_verified_collection(row, result)
    row.refresh_from_db()
    return row


def _apply_verified_collection(collection, result):
    # Invoice before collection is the common lock order for ledger updates.
    with transaction.atomic():
        invoice = Invoice.objects.select_for_update().get(pk=collection.invoice_id)
        row = Collection.objects.select_for_update().get(pk=collection.pk)
        now = timezone.now()
        row.last_checked_at = now
        _apply_collection_result(row, invoice, result, now)
        if (
            row.status == Collection.Status.SUCCESSFUL
            and not row.settled
            and not row.issue
            and now - row.created_at > SETTLEMENT_OVERDUE
        ):
            row.issue = "settlement_overdue"
        row.next_check_at = collection_next_check(row, now)
        row.save()


def _expire_if_unpaid(row, now):
    if row.status == Collection.Status.PENDING and checkout_window_over(row, now):
        row.status, row.issue = Collection.Status.EXPIRED, "checkout_not_completed"


def _paid_on(data, now):
    """The day Lenco completed the payment, so a late check never makes rent late."""
    completed = parse_stamp(data.get("completedAt"))
    if completed is None or completed > now + timedelta(minutes=5):
        return timezone.localdate(now)
    return timezone.localdate(completed)


def _apply_collection_result(row, invoice, result, now):
    if not _valid_data(result):
        if result.http_status == 404 and result.error == "http_error":
            # Lenco has no payment under this reference: not paid, at least yet.
            row.issue = ""
            _expire_if_unpaid(row, now)
        else:
            row.issue = result.error or "provider_not_ready"
        return
    data = result.payload["data"]
    try:
        valid = (
            data.get("reference") == row.reference
            and money(data.get("amount"), positive=True) == row.amount
            and data.get("currency") == row.currency
            and isinstance(data.get("id"), str)
            and 0 < len(data["id"]) <= 100
        )
        if row.channel == "mobile-money" and data.get("status") == "successful":
            payer = data.get("mobileMoneyDetails") or {}
            valid = (
                valid
                and data.get("type") == "mobile-money"
                and isinstance(payer, dict)
                and normalize_phone(payer.get("phone", "")) == row.payer_phone
                and payer.get("operator") == row.payer_operator
                and payer.get("country") == "zm"
            )
        if row.channel == "card" and data.get("status") == "successful":
            valid = valid and data.get("type") == "card"
    except ValidationError:
        valid = False
    if not valid:
        _issue(row, "collection_details_mismatch")
        return
    if row.provider_id and row.provider_id != data["id"]:
        _issue(row, "collection_identity_changed")
        return
    if not row.provider_id:
        # The unique constraint catches one Lenco payment claimed by two rows.
        try:
            with transaction.atomic():
                row.provider_id = data["id"]
                row.save(update_fields=["provider_id"])
        except IntegrityError:
            row.refresh_from_db()
            row.last_checked_at = now
            _issue(row, "duplicate_provider_collection")
            return
    state = data.get("status")
    row.provider_state = {
        **row.provider_state,
        "status": state if isinstance(state, str) else None,
        "completed_at": stamp(parse_stamp(data.get("completedAt"))),
    }
    if state == "successful":
        _record_success(row, invoice, data, now)
    elif state == "failed" and row.status != Collection.Status.SUCCESSFUL:
        row.status, row.issue = Collection.Status.FAILED, "collection_failed"
    else:
        # Pending/out-of-order responses cannot undo a receipt or settlement.
        _expire_if_unpaid(row, now)


def _record_success(row, invoice, data, now):
    row.issue = ""
    if row.payment_id is None:
        if invoice.status == Invoice.Status.VOID or row.amount > invoice.balance:
            _issue(row, "received_money_needs_allocation")
            return
        method = {"mobile-money": Payment.Method.MOBILE_MONEY, "card": Payment.Method.CARD}
        if not isinstance(data.get("type"), str) or data["type"] not in method:
            _issue(row, "unexpected_payment_channel")
            return
        # One receipt per collection: payment_id is checked under the row lock.
        row.payment = record_payment(
            invoice=invoice,
            amount=row.amount,
            method=method[data["type"]],
            paid_on=_paid_on(data, now),
            reference=row.reference,
            notes="Verified Lenco online rent payment.",
        )
    row.status = Collection.Status.SUCCESSFUL
    try:
        if data.get("fee") is not None:
            row.fee = money(data["fee"])
        settlement = data.get("settlement")
        if data.get("settlementStatus") == "settled":
            if (
                not isinstance(settlement, dict)
                or settlement.get("status") != "settled"
                or settlement.get("currency") != row.currency
                or settlement.get("accountId") != row.debit_account_id
            ):
                raise ValidationError("Settlement mismatch")
            net = money(settlement.get("amountSettled"), positive=True)
            if net > row.amount or (row.settled_amount is not None and row.settled_amount != net):
                raise ValidationError("Settlement amount mismatch")
            row.settled, row.settled_amount = True, net
            # Settled rent joins the landlord's balance for withdrawal. Only the
            # legacy setting still pays each collection out on its own.
            if settings.LENCO_AUTOMATIC_PAYOUTS:
                Payout.objects.get_or_create(
                    collection=row, defaults={"amount": net, "next_check_at": now}
                )
    except ValidationError:
        row.issue = "settlement_details_mismatch"


def _apply_payout_result(payout, result):
    with transaction.atomic():
        row = (
            Payout.objects.select_for_update(of=("self",))
            .select_related("collection__destination")
            .get(pk=payout.pk)
        )
        now = timezone.now()
        row.last_checked_at = now
        _apply_payout_data(row, result, now)
        row.next_check_at = payout_next_check(row, now)
        row.save()


def _apply_payout_data(row, result, now):
    if row.status == Payout.Status.SUCCESSFUL:
        return
    if not _valid_data(result):
        row.issue = result.error or "payout_not_confirmed"
        return
    data, collection = result.payload["data"], row.collection
    recipient = data.get("creditAccount") or {}
    try:
        valid = (
            data.get("reference") == row.reference
            and money(data.get("amount"), positive=True) == row.amount
            and data.get("currency") == collection.currency
            and data.get("accountId") == collection.debit_account_id
            and recipient.get("type") == "mobile-money"
            and normalize_phone(recipient.get("phone", "")) == collection.destination.phone
            and recipient.get("operator") == collection.destination.operator
            and isinstance(data.get("id"), str)
            and 0 < len(data["id"]) <= 100
        )
    except (ValidationError, AttributeError):
        valid = False
    if not valid or (row.provider_id and row.provider_id != data.get("id")):
        row.status, row.issue = Payout.Status.REVIEW, "payout_details_mismatch"
        return
    row.provider_id = data["id"]
    if not isinstance(data.get("status"), str) or data["status"] not in {
        "pending",
        "successful",
        "failed",
    }:
        return
    row.status = data["status"]
    if row.status == Payout.Status.SUCCESSFUL and row.confirmed_at is None:
        row.confirmed_at = now
    row.issue = "payout_failed" if row.status == Payout.Status.FAILED else ""
    try:
        row.fee = money(data["fee"]) if data.get("fee") is not None else None
    except ValidationError:
        row.issue = "invalid_payout_fee"


def normalize_phone(phone):
    import re

    phone = re.sub(r"[\s()-]", "", str(phone))
    if re.fullmatch(r"0[79]\d{8}", phone):
        phone = "+260" + phone[1:]
    elif re.fullmatch(r"260[79]\d{8}", phone):
        phone = "+" + phone
    if not re.fullmatch(r"\+260[79]\d{8}", phone):
        raise ValidationError("Enter a valid Zambia mobile-money number.")
    return phone


def process_payout(payout):
    """Submit a queued payout once, or ask Lenco about a submitted one."""
    # Commit the claim BEFORE sending. Crash/timeout => query the same reference;
    # never make a second debit merely because we didn't receive an answer.
    with transaction.atomic():
        row = (
            Payout.objects.select_for_update(of=("self",))
            .select_related("collection__destination", "collection__organization")
            .get(pk=payout.pk)
        )
        collection = row.collection
        now = timezone.now()
        if row.status in {Payout.Status.SUCCESSFUL, Payout.Status.REVIEW}:
            if row.next_check_at:
                row.next_check_at = None
                row.save(update_fields=["next_check_at", "updated_at"])
            return
        submit = row.status == Payout.Status.QUEUED
        if submit:
            if not settings.LENCO_PAYOUTS_ENABLED:
                row.next_check_at = now + timedelta(minutes=15)
                row.save(update_fields=["next_check_at", "updated_at"])
                return
            if (
                not collection.settled
                or collection.status != "successful"
                or collection.issue
                or not collection.payment_id
                or row.amount != collection.settled_amount
                or not collection.destination.enabled
                or not collection.organization.is_active
                or collection.debit_account_id != settings.LENCO_DEBIT_ACCOUNT_ID
            ):
                row.status, row.issue = Payout.Status.REVIEW, "payout_requires_review"
                row.next_check_at = None
                row.save()
                return
            from .balances import can_reserve_payout

            if not can_reserve_payout(row):
                row.issue = "awaiting_balance_reconciliation"
                row.next_check_at = now + timedelta(minutes=1)
                row.save()
                return
            row.status, row.issue = Payout.Status.SUBMITTING, ""
            row.submitted_at = row.last_checked_at = now
            row.next_check_at = payout_next_check(row, now)
            row.save()
        elif row.status != Payout.Status.FAILED and (
            now - (row.submitted_at or row.created_at) > PAYOUT_CONFIRMATION_LIMIT
        ):
            row.status, row.issue = Payout.Status.REVIEW, "payout_unconfirmed"
            row.next_check_at = None
            row.save()
            return
    provider = Provider(collection.environment)
    if submit:
        destination = collection.destination
        payload = {
            "accountId": collection.debit_account_id,
            "amount": float(row.amount),
            "reference": row.reference,
            "phone": destination.phone,
            "operator": destination.operator,
            "country": "zm",
            "narration": f"Rent {collection.reference}",
        }
        result = provider.request(
            "payout_submit", collection=collection, payout=row, payload=payload
        )
    else:
        # A failed payout is only asked again when a webhook wakes it.
        result = provider.request("payout_status", collection=collection, payout=row)
    _apply_payout_result(row, result)
