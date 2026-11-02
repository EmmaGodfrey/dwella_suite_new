from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.common.models import OrganizationScopedModel


class Invoice(OrganizationScopedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PARTIALLY_PAID = "partially_paid", "Part paid"
        PAID = "paid", "Paid"
        VOID = "void", "Void"

    # Still owed money; "overdue" is these past their due date, worked out at
    # query time so it can never go stale.
    UNPAID_STATUSES = (Status.OPEN, Status.PARTIALLY_PAID)

    reference = models.CharField(max_length=20)
    lease = models.ForeignKey(
        "leases.Lease", on_delete=models.PROTECT, related_name="invoices", blank=True, null=True
    )
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="invoices")
    unit = models.ForeignKey(
        "properties.Unit", on_delete=models.PROTECT, related_name="invoices", blank=True, null=True
    )
    # Set for monthly rent invoices (first day of the month billed); empty for
    # one-off charges. Unique per lease so generation can safely re-run.
    period_start = models.DateField(blank=True, null=True)
    issue_date = models.DateField()
    due_date = models.DateField()
    # Kept in step with the lines and payments by the billing services, so
    # lists and balances never need to re-add every line.
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    voided_at = models.DateTimeField(blank=True, null=True)
    # A late fee raised after an invoice was sent to ZRA cannot be added to
    # it, so it is billed on its own invoice that points back here.
    charged_for = models.ForeignKey(
        "self", on_delete=models.PROTECT, related_name="follow_up_invoices", blank=True, null=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-issue_date", "-created_at"]
        indexes = [
            models.Index(fields=["organization", "status", "due_date"]),
            models.Index(fields=["organization", "period_start"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "reference"],
                name="unique_invoice_reference_per_organization",
            ),
            models.UniqueConstraint(
                fields=["lease", "period_start"],
                condition=Q(period_start__isnull=False) & ~Q(status="void"),
                name="one_rent_invoice_per_lease_period",
            ),
            models.CheckConstraint(
                condition=Q(amount_paid__lte=F("total")), name="invoice_not_overpaid"
            ),
        ]

    @property
    def balance(self):
        return self.total - self.amount_paid

    def __str__(self):
        return self.reference


class InvoiceLine(models.Model):
    class Kind(models.TextChoices):
        RENT = "rent", "Rent"
        LATE_FEE = "late_fee", "Late fee"
        UTILITY = "utility", "Utility"
        DEPOSIT = "deposit", "Deposit"
        OTHER = "other", "Other"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OTHER)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="invoice_line_amount_positive")
        ]

    def __str__(self):
        return f"{self.invoice} - {self.description}"


class Payment(OrganizationScopedModel):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        MOBILE_MONEY = "mobile_money", "Mobile money"
        BANK_TRANSFER = "bank_transfer", "Bank transfer"
        CARD = "card", "Card"
        CHEQUE = "cheque", "Cheque"
        # Settled from the tenant's security deposit by an applied deduction.
        DEPOSIT = "deposit", "From security deposit"

    # Methods a manager can choose when recording money they received.
    RECEIVED_METHODS = [choice for choice in Method.choices if choice[0] != "deposit"]

    receipt_number = models.CharField(max_length=20)
    reversed_at = models.DateTimeField(blank=True, null=True)
    reversal_reason = models.CharField(max_length=500, blank=True)
    reversed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reversed_payments",
        blank=True,
        null=True,
    )
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    paid_on = models.DateField()
    # Mobile-money transaction id, bank reference or cheque number.
    reference = models.CharField(max_length=80, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_payments",
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-paid_on", "-created_at"]
        indexes = [models.Index(fields=["organization", "paid_on"])]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "receipt_number"],
                name="unique_receipt_number_per_organization",
            ),
            models.CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_positive"),
        ]

    def __str__(self):
        return self.receipt_number


class PaymentInstruction(OrganizationScopedModel):
    """How tenants can pay the workspace directly; printed on every invoice.

    Separate from the payout destination: where Dwella sends withdrawals is not
    automatically where tenants should pay."""

    MAX_PER_WORKSPACE = 3

    class Kind(models.TextChoices):
        BANK = "bank", "Bank transfer"
        MOBILE_MONEY = "mobile_money", "Mobile money"

    class Network(models.TextChoices):
        AIRTEL = "airtel", "Airtel Money"
        MTN = "mtn", "MTN Mobile Money"
        ZAMTEL = "zamtel", "Zamtel Money"

    kind = models.CharField(max_length=12, choices=Kind.choices)
    account_name = models.CharField(max_length=120)
    bank_name = models.CharField(max_length=120, blank=True)
    branch = models.CharField(max_length=120, blank=True)
    account_number = models.CharField(max_length=34, blank=True)
    network = models.CharField(max_length=10, choices=Network.choices, blank=True)
    phone = models.CharField(max_length=16, blank=True)
    note = models.CharField(max_length=200, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"{self.get_kind_display()} · {self.account_name}"

    def as_snapshot(self):
        if self.kind == self.Kind.BANK:
            lines = [
                ("Bank", self.bank_name),
                ("Branch", self.branch),
                ("Account name", self.account_name),
                ("Account number", self.account_number),
            ]
        else:
            lines = [
                ("Network", self.get_network_display()),
                ("Number", self.phone),
                ("Registered name", self.account_name),
            ]
        return {
            "title": self.get_kind_display(),
            "lines": [[label, value] for label, value in lines if value],
            "note": self.note,
        }


class DepositDeduction(OrganizationScopedModel):
    """A proposed deduction from a tenant's deposit. It only reserves money
    until it is applied; the tenant can accept or dispute it first."""

    class Status(models.TextChoices):
        PROPOSED = "proposed", "Awaiting tenant response"
        ACCEPTED = "accepted", "Accepted by tenant"
        DISPUTED = "disputed", "Disputed by tenant"
        APPLIED = "applied", "Deducted"
        WITHDRAWN = "withdrawn", "Withdrawn"

    # Still holding money back from a refund.
    OPEN_STATUSES = (Status.PROPOSED, Status.ACCEPTED, Status.DISPUTED)

    lease = models.ForeignKey(
        "leases.Lease", on_delete=models.PROTECT, related_name="deposit_deductions"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PROPOSED, db_index=True
    )
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    tenant_note = models.TextField(blank=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    resolution_note = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", blank=True, null=True
    )
    decided_at = models.DateTimeField(blank=True, null=True)
    # Unpaid rent or charges this deduction pays once it is applied.
    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, related_name="deposit_deductions", blank=True, null=True
    )
    payment = models.OneToOneField(
        Payment, on_delete=models.PROTECT, related_name="deposit_deduction", blank=True, null=True
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0), name="deposit_deduction_amount_positive"
            )
        ]

    def __str__(self):
        return f"{self.lease} - {self.reason}"


class DepositEntry(OrganizationScopedModel):
    """Append-only deposit ledger. Positive entries add to what is held for the
    tenant, negative ones reduce it; corrections are new entries, never edits."""

    class Kind(models.TextChoices):
        OPENING = "opening", "Deposit already held"
        COLLECTED = "collected", "Deposit collected"
        DEDUCTION = "deduction", "Deduction applied"
        REFUND = "refund", "Refund paid"
        TRANSFER_IN = "transfer_in", "Carried over from previous lease"
        TRANSFER_OUT = "transfer_out", "Carried over to renewal"
        # An applied deduction undone because the payment it made was reversed.
        RETURNED = "returned", "Returned to deposit"

    lease = models.ForeignKey(
        "leases.Lease", on_delete=models.PROTECT, related_name="deposit_entries"
    )
    kind = models.CharField(max_length=14, choices=Kind.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    occurred_on = models.DateField()
    # A collected entry follows its deposit invoice's payments (and reversals).
    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, related_name="deposit_entries", blank=True, null=True
    )
    deduction = models.OneToOneField(
        DepositDeduction, on_delete=models.PROTECT, related_name="entry", blank=True, null=True
    )
    method = models.CharField(max_length=20, choices=Payment.Method.choices, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    note = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+", blank=True, null=True
    )

    class Meta:
        ordering = ["-occurred_on", "-created_at"]
        indexes = [models.Index(fields=["lease", "kind"])]
        constraints = [
            models.CheckConstraint(condition=~Q(amount=0), name="deposit_entry_amount_nonzero")
        ]

    def __str__(self):
        return f"{self.lease} - {self.get_kind_display()} {self.amount}"


class DepositEvidence(OrganizationScopedModel):
    """A photo or document supporting a deduction. Stored privately in the
    database (images re-encoded without metadata) and served only to the
    workspace and the tenant concerned."""

    MAX_PER_DEDUCTION = 5

    deduction = models.ForeignKey(
        DepositDeduction, on_delete=models.CASCADE, related_name="evidence"
    )
    name = models.CharField(max_length=120)
    content_type = models.CharField(max_length=40)
    content = models.BinaryField()
    size = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.name
