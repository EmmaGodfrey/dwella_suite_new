import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.common.models import TimeStampedModel, UUIDModel


def collection_reference():
    return f"rent-{uuid.uuid4().hex}"


def payout_reference():
    return f"payout-{uuid.uuid4().hex}"


def withdrawal_reference():
    return f"withdrawal-{uuid.uuid4().hex}"


class Destination(UUIDModel, TimeStampedModel):
    """Versioned destination. Account details/approval are never edited in place."""

    class Kind(models.TextChoices):
        MOBILE_MONEY = "mobile-money", "Mobile money"
        BANK_ACCOUNT = "bank-account", "Bank account"

    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT)
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.MOBILE_MONEY)
    phone = models.CharField(max_length=16, blank=True)
    operator = models.CharField(max_length=10, blank=True)
    bank_id = models.CharField(max_length=64, blank=True)
    bank_name = models.CharField(max_length=180, blank=True)
    account_number = models.CharField(max_length=34, blank=True)
    account_name = models.CharField(max_length=180)
    # The registered name Lenco returned for this account; empty if not checked.
    lookup_name = models.CharField(max_length=180, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    approval_reason = models.CharField(max_length=500)
    enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization"],
                condition=Q(enabled=True),
                name="one_enabled_payout_destination",
            )
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            immutable = (
                "organization_id",
                "kind",
                "phone",
                "operator",
                "bank_id",
                "bank_name",
                "account_number",
                "account_name",
                "lookup_name",
                "approved_by_id",
                "approval_reason",
            )
            if any(getattr(old, key) != getattr(self, key) for key in immutable):
                raise ValueError("Create a new destination version instead of editing approval.")
        return super().save(*args, **kwargs)


class Collection(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Awaiting payment"
        SUCCESSFUL = "successful", "Paid"
        FAILED = "failed", "Failed"
        REVIEW = "review", "Needs reconciliation"
        # Never completed in its checkout window; a late webhook can still revive it.
        EXPIRED = "expired", "Expired"

    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT)
    invoice = models.ForeignKey("billing.Invoice", on_delete=models.PROTECT)
    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    destination = models.ForeignKey(Destination, on_delete=models.PROTECT)
    environment = models.CharField(max_length=7)
    idempotency_key = models.UUIDField()
    # Existing attempts keep the original hosted flow during rollout.
    channel = models.CharField(
        max_length=12,
        default="checkout",
        choices=[
            ("checkout", "Hosted checkout"),
            ("card", "Card"),
            ("mobile-money", "Mobile money"),
        ],
    )
    payer_phone = models.CharField(max_length=16, blank=True)
    payer_operator = models.CharField(max_length=10, blank=True)
    collection_submitted_at = models.DateTimeField(null=True)
    reference = models.CharField(max_length=50, default=collection_reference, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="ZMW")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    provider_id = models.CharField(max_length=100, blank=True)
    fee = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    settled_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    settled = models.BooleanField(default=False)
    debit_account_id = models.CharField(max_length=36)
    payment = models.OneToOneField("billing.Payment", on_delete=models.PROTECT, null=True)
    issue = models.CharField(max_length=60, blank=True)
    last_checked_at = models.DateTimeField(null=True)
    # When the worker should ask Lenco again; empty once nothing can change.
    next_check_at = models.DateTimeField(null=True)
    # Latest provider facts kept on the row instead of in extra tables:
    # {"status": ..., "completed_at": ..., "webhook_at": ...}.
    provider_state = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "initiated_by", "idempotency_key"],
                name="unique_rent_checkout_key",
            ),
            models.UniqueConstraint(
                fields=["environment", "provider_id"],
                condition=~Q(provider_id=""),
                name="unique_lenco_collection",
            ),
            models.UniqueConstraint(
                fields=["invoice"],
                condition=Q(status="pending"),
                name="one_pending_checkout_per_invoice",
            ),
            models.CheckConstraint(condition=Q(amount__gt=0), name="rent_collection_positive"),
        ]
        indexes = [
            models.Index(
                fields=["next_check_at"],
                condition=Q(next_check_at__isnull=False),
                name="payments_collection_due",
            )
        ]


class Payout(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        SUBMITTING = "submitting", "Submitting"
        PENDING = "pending", "Processing"
        SUCCESSFUL = "successful", "Delivered"
        FAILED = "failed", "Failed"
        REVIEW = "review", "Needs reconciliation"

    collection = models.OneToOneField(Collection, on_delete=models.PROTECT, related_name="payout")
    reference = models.CharField(max_length=50, default=payout_reference, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.QUEUED)
    provider_id = models.CharField(max_length=100, blank=True)
    fee = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    issue = models.CharField(max_length=60, blank=True)
    last_checked_at = models.DateTimeField(null=True)
    submitted_at = models.DateTimeField(null=True)
    confirmed_at = models.DateTimeField(null=True)
    next_check_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="rent_payout_positive")
        ]
        indexes = [
            models.Index(
                fields=["next_check_at"],
                condition=Q(next_check_at__isnull=False),
                name="payments_payout_due",
            ),
            # The gateway ledger matches provider records to payouts by this ID.
            models.Index(
                fields=["provider_id"],
                condition=~Q(provider_id=""),
                name="payments_payout_provider",
            ),
        ]


class Withdrawal(UUIDModel, TimeStampedModel):
    """A landlord-requested transfer of settled rent to their receiving account.

    The landlord enters the amount they receive; the highest Lenco fee for that
    amount is reserved on top. Lenco's reported fee is charged once known, up
    to the reserve, so the balance never pays more than was confirmed.
    """

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        SUBMITTING = "submitting", "Submitting"
        PENDING = "pending", "Processing"
        SUCCESSFUL = "successful", "Delivered"
        FAILED = "failed", "Failed"
        REVIEW = "review", "Needs reconciliation"
        CANCELLED = "cancelled", "Cancelled"

    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT)
    destination = models.ForeignKey(Destination, on_delete=models.PROTECT)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    environment = models.CharField(max_length=7)
    debit_account_id = models.CharField(max_length=36)
    idempotency_key = models.UUIDField()
    reference = models.CharField(max_length=50, default=withdrawal_reference, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    fee_reserved = models.DecimalField(max_digits=12, decimal_places=2)
    fee = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    fee_charged = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.QUEUED)
    provider_id = models.CharField(max_length=100, blank=True)
    issue = models.CharField(max_length=60, blank=True)
    last_checked_at = models.DateTimeField(null=True)
    submitted_at = models.DateTimeField(null=True)
    confirmed_at = models.DateTimeField(null=True)
    next_check_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "requested_by", "idempotency_key"],
                name="unique_withdrawal_key",
            ),
            models.CheckConstraint(condition=Q(amount__gt=0), name="withdrawal_positive"),
            models.CheckConstraint(
                condition=Q(fee_reserved__gte=0), name="withdrawal_fee_reserved_positive"
            ),
        ]
        indexes = [
            models.Index(
                fields=["next_check_at"],
                condition=Q(next_check_at__isnull=False),
                name="payments_withdrawal_due",
            ),
            models.Index(
                fields=["provider_id"],
                condition=~Q(provider_id=""),
                name="payments_withdrawal_provider",
            ),
            models.Index(fields=["organization", "status"], name="payments_withdrawal_org"),
        ]


class Exchange(UUIDModel):
    """Append-only, encrypted, redacted provider evidence; no auth headers."""

    created_at = models.DateTimeField(auto_now_add=True)
    collection = models.ForeignKey(Collection, on_delete=models.PROTECT, null=True)
    payout = models.ForeignKey(Payout, on_delete=models.PROTECT, null=True)
    withdrawal = models.ForeignKey(Withdrawal, on_delete=models.PROTECT, null=True)
    environment = models.CharField(max_length=7)
    operation = models.CharField(max_length=40)
    http_status = models.PositiveSmallIntegerField(null=True)
    body_sha256 = models.CharField(max_length=64)
    encrypted_payload = models.BinaryField(editable=False)
    error = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ["-created_at"]
        # Finds the latest read of the same thing, to skip storing repeats.
        indexes = [models.Index(fields=["operation", "-id"], name="payments_exchange_latest")]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("Provider evidence is append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Provider evidence is append-only.")


class ProviderAccount(UUIDModel, TimeStampedModel):
    environment = models.CharField(max_length=7)
    account_id = models.UUIDField()
    currency = models.CharField(max_length=3)
    opening_balance = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    # Start of the latest sync; the latest snapshot describes its outcome.
    checked_at = models.DateTimeField(null=True)
    # Set when an incremental import disagrees; the next sync reads everything.
    full_scan_needed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "account_id"], name="unique_lenco_account_ledger"
            )
        ]


class ProviderTransaction(models.Model):
    """Immutable imported credit/debit, linked to the encrypted original response."""

    account = models.ForeignKey(ProviderAccount, on_delete=models.PROTECT)
    provider_id = models.CharField(max_length=100)
    kind = models.CharField(max_length=6)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    posted_at = models.DateTimeField()
    content_digest = models.CharField(max_length=64)
    exchange = models.ForeignKey(Exchange, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account", "provider_id"], name="unique_imported_lenco_transaction"
            )
        ]

    def __str__(self):
        return self.provider_id


class BalanceSnapshot(UUIDModel):
    account = models.ForeignKey(ProviderAccount, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    available_balance = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    ledger_balance = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    expected_balance = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    difference = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    # Settled rent not yet paid out or in flight, and the ledger above it.
    held_for_landlords = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    surplus = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    rent_collections_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    rent_settled_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    payouts_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    payout_fees_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credits_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    debits_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    transaction_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16)  # baseline, matched, mismatch, shortfall, incomplete
    issue = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["-created_at"]
