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

    receipt_number = models.CharField(max_length=20)
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
