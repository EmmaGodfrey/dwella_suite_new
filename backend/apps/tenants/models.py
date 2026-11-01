from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from apps.common.models import OrganizationScopedModel


class Tenant(OrganizationScopedModel):
    class TenantType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        COMPANY = "company", "Company"

    class IdentityType(models.TextChoices):
        NRC = "nrc", "NRC"
        PASSPORT = "passport", "Passport"
        OTHER = "other", "Other identity document"

    class Status(models.TextChoices):
        APPLICANT = "applicant", "Applicant"
        ACTIVE = "active", "Active"
        PAST = "past", "Past"

    full_name = models.CharField(max_length=180)
    # Stored in E.164 (`+260971234567`): it is the mobile-money wallet and the
    # SMS/WhatsApp address, so one tenant per number per organization.
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    national_id = models.CharField(max_length=40, blank=True)
    tenant_type = models.CharField(max_length=12, choices=TenantType.choices, default="individual")
    identity_type = models.CharField(max_length=12, choices=IdentityType.choices, default="nrc")
    identity_country = models.CharField(max_length=2, default="ZM")
    billing_address = models.TextField(blank=True, max_length=1000)
    company_registration = models.CharField(max_length=80, blank=True)
    representative_name = models.CharField(max_length=180, blank=True)
    representative_phone = models.CharField(max_length=20, blank=True)
    document_requirements_since = models.DateTimeField(default=timezone.now)
    # Printed on Smart Invoices; businesses renting commercial space need it.
    tpin = models.CharField(
        max_length=10,
        blank=True,
        validators=[RegexValidator(r"^[0-9]{10}$", "A TPIN is 10 digits.")],
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.APPLICANT, db_index=True
    )
    # Set once the tenant accepts their invite and signs in to the tenant app.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tenant_records",
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["full_name"]
        indexes = [models.Index(fields=["organization", "status"])]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "phone_number"],
                name="unique_tenant_phone_per_organization",
            )
        ]

    def __str__(self):
        return self.full_name

