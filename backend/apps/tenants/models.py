from django.conf import settings
from django.db import models

from apps.common.models import OrganizationScopedModel


class Tenant(OrganizationScopedModel):
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
