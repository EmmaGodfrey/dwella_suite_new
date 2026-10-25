import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.common.models import TimeStampedModel, UUIDModel


def collection_reference():
    return f"rent-{uuid.uuid4().hex}"


def payout_reference():
    return f"payout-{uuid.uuid4().hex}"


class Destination(UUIDModel, TimeStampedModel):
    """Versioned destination. Phone/operator/approval are never edited in place."""

    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT)
    phone = models.CharField(max_length=16)
    operator = models.CharField(max_length=10)
    account_name = models.CharField(max_length=180)
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
                "phone",
                "operator",
                "account_name",
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

    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT)
    invoice = models.ForeignKey("billing.Invoice", on_delete=models.PROTECT)
    initiated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    destination = models.ForeignKey(Destination, on_delete=models.PROTECT)
    environment = models.CharField(max_length=7)
    idempotency_key = models.UUIDField()
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
        indexes = [models.Index(fields=["status", "last_checked_at"])]


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

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="rent_payout_positive")
        ]
        indexes = [models.Index(fields=["status", "last_checked_at"])]


class Exchange(UUIDModel):
    """Append-only, encrypted, redacted provider evidence; no auth headers."""

    created_at = models.DateTimeField(auto_now_add=True)
    collection = models.ForeignKey(Collection, on_delete=models.PROTECT, null=True)
    payout = models.ForeignKey(Payout, on_delete=models.PROTECT, null=True)
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


class WebhookReceipt(TimeStampedModel):
    environment = models.CharField(max_length=7)
    digest = models.CharField(max_length=64)
    reference = models.CharField(max_length=50)
    event = models.CharField(max_length=40)
    exchange = models.OneToOneField(Exchange, on_delete=models.PROTECT)
    processed_at = models.DateTimeField(null=True)
    last_attempt_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "digest"], name="unique_lenco_webhook_body"
            )
        ]


class ProviderAccount(UUIDModel, TimeStampedModel):
    environment = models.CharField(max_length=7)
    account_id = models.UUIDField()
    currency = models.CharField(max_length=3)
    opening_balance = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    app_opening_balance = models.DecimalField(max_digits=18, decimal_places=2, null=True)

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
    app_expected_balance = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    app_difference = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    rent_collections_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    rent_settled_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    payouts_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    payout_fees_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credits_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    debits_total = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    transaction_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16)  # baseline, matched, mismatch, incomplete
    issue = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["-created_at"]
