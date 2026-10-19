from django.db import models
from django.db.models import F, Q

from apps.common.models import OrganizationScopedModel


class Lease(OrganizationScopedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_SIGNATURE = "pending_signature", "Awaiting signature"
        ACTIVE = "active", "Active"
        ENDED = "ended", "Ended"

    # Draft and awaiting-signature leases already hold the unit: two people
    # cannot both be signing for the same home.
    OPEN_STATUSES = (Status.DRAFT, Status.PENDING_SIGNATURE, Status.ACTIVE)

    reference = models.CharField(max_length=20)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="leases")
    unit = models.ForeignKey("properties.Unit", on_delete=models.PROTECT, related_name="leases")
    start_date = models.DateField()
    end_date = models.DateField()
    monthly_rent = models.DecimalField(max_digits=12, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rent_due_day = models.PositiveSmallIntegerField(default=1)
    late_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    late_fee_grace_days = models.PositiveSmallIntegerField(default=5)
    notice_period_months = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    activated_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]
        indexes = [models.Index(fields=["organization", "status"])]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "reference"],
                name="unique_lease_reference_per_organization",
            ),
            models.UniqueConstraint(
                fields=["unit"],
                condition=Q(status__in=["draft", "pending_signature", "active"]),
                name="one_open_lease_per_unit",
            ),
            models.CheckConstraint(
                condition=Q(end_date__gt=F("start_date")),
                name="lease_ends_after_it_starts",
            ),
            models.CheckConstraint(
                condition=Q(rent_due_day__gte=1, rent_due_day__lte=28),
                name="lease_rent_due_day_in_range",
            ),
        ]

    def __str__(self):
        return f"{self.reference} - {self.tenant}"
