from django.core.validators import RegexValidator
from django.db import models

from apps.common.models import OrganizationScopedModel, TimeStampedModel

from .zra.codes import TaxCategory

tpin_validator = RegexValidator(r"^\d{10}$", "A TPIN is 10 digits.")


class SmartInvoiceSettings(TimeStampedModel):
    """A workspace's link to ZRA Smart Invoice through its VSDC device."""

    organization = models.OneToOneField(
        "organizations.Organization", on_delete=models.CASCADE, related_name="smart_invoice"
    )
    enabled = models.BooleanField(default=False)
    tpin = models.CharField(max_length=10, validators=[tpin_validator])
    branch_id = models.CharField(max_length=3, default="000")
    device_serial = models.CharField(max_length=100)
    # Letting a home is normally VAT exempt and letting business premises
    # standard rated; both stay editable because the landlord's tax position
    # (VAT registered, turnover tax) decides what actually applies.
    residential_tax_category = models.CharField(
        max_length=3, choices=TaxCategory.choices, default=TaxCategory.EXEMPT
    )
    commercial_tax_category = models.CharField(
        max_length=3, choices=TaxCategory.choices, default=TaxCategory.STANDARD
    )
    # Filled in by device initialisation.
    taxpayer_name = models.CharField(max_length=60, blank=True)
    sdc_id = models.CharField(max_length=12, blank=True)
    mrc_no = models.CharField(max_length=11, blank=True)
    initialized_at = models.DateTimeField(blank=True, null=True)
    # invcNo is a running number per device, shared by sales and refunds.
    last_invoice_number = models.PositiveBigIntegerField(default=0)

    class Meta:
        verbose_name = "Smart Invoice settings"
        verbose_name_plural = "Smart Invoice settings"

    @property
    def is_ready(self):
        return self.enabled and self.initialized_at is not None

    def __str__(self):
        return f"Smart Invoice · {self.organization}"


class FiscalReceipt(OrganizationScopedModel):
    """One invoice (or its credit note) as recorded by ZRA."""

    class Kind(models.TextChoices):
        SALE = "sale", "Invoice"
        REFUND = "refund", "Credit note"

    class Status(models.TextChoices):
        PENDING = "pending", "Sending"
        ISSUED = "issued", "Issued"
        FAILED = "failed", "Failed"
        # Never reached ZRA and no longer needed (its invoice was voided).
        CANCELLED = "cancelled", "Cancelled"

    invoice = models.ForeignKey(
        "billing.Invoice", on_delete=models.PROTECT, related_name="fiscal_receipts"
    )
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.SALE)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    invoice_number = models.PositiveBigIntegerField()
    original_invoice_number = models.PositiveBigIntegerField(blank=True, null=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2)
    # What ZRA answered with; printed on the invoice.
    receipt_number = models.PositiveBigIntegerField(blank=True, null=True)
    total_receipt_number = models.PositiveBigIntegerField(blank=True, null=True)
    internal_data = models.CharField(max_length=60, blank=True)
    signature = models.CharField(max_length=60, blank=True)
    sdc_id = models.CharField(max_length=12, blank=True)
    mrc_no = models.CharField(max_length=11, blank=True)
    issued_at = models.DateTimeField(blank=True, null=True)
    request_payload = models.JSONField(default=dict)
    response_payload = models.JSONField(blank=True, null=True)
    error_code = models.CharField(max_length=5, blank=True)
    error_message = models.CharField(max_length=255, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(fields=["invoice", "kind"], name="one_fiscal_receipt_per_kind"),
            models.UniqueConstraint(
                fields=["organization", "invoice_number"],
                name="unique_fiscal_invoice_number_per_organization",
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} {self.invoice_number} ({self.invoice})"
