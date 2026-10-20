from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.common.models import OrganizationScopedModel, TimeStampedModel


def maintenance_photo_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"maintenance/photos/{uuid4().hex}.{extension}"


class Vendor(OrganizationScopedModel):
    """A contractor the landlord sends work to."""

    name = models.CharField(max_length=180)
    trade = models.CharField(max_length=80, blank=True)
    contact_name = models.CharField(max_length=180, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"], name="unique_vendor_name_per_organization"
            )
        ]

    def __str__(self):
        return self.name


class MaintenanceRequest(OrganizationScopedModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Category(models.TextChoices):
        PLUMBING = "plumbing", "Plumbing"
        ELECTRICAL = "electrical", "Electrical"
        ROOFING = "roofing", "Roofing"
        APPLIANCES = "appliances", "Appliances"
        SECURITY = "security", "Security & locks"
        PAINTING = "painting", "Painting & walls"
        PEST_CONTROL = "pest_control", "Pest control"
        GROUNDS = "grounds", "Grounds & cleaning"
        GENERAL = "general", "General"

    class Source(models.TextChoices):
        LANDLORD = "landlord", "Landlord"
        TENANT = "tenant", "Tenant"
        CARETAKER = "caretaker", "Caretaker"
        INSPECTION = "inspection", "Inspection"

    OPEN_STATUSES = (Status.NEW, Status.SCHEDULED, Status.IN_PROGRESS)

    reference = models.CharField(max_length=20)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    property = models.ForeignKey(
        "properties.Property", on_delete=models.PROTECT, related_name="maintenance_requests"
    )
    # Empty for common areas (gate, roof, grounds).
    unit = models.ForeignKey(
        "properties.Unit",
        on_delete=models.PROTECT,
        related_name="maintenance_requests",
        blank=True,
        null=True,
    )
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.SET_NULL,
        related_name="maintenance_requests",
        blank=True,
        null=True,
    )
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.NORMAL, db_index=True
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW, db_index=True
    )
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.LANDLORD)
    access_notes = models.CharField(max_length=200, blank=True)
    permission_to_enter = models.BooleanField(default=False)
    vendor = models.ForeignKey(
        Vendor, on_delete=models.PROTECT, related_name="requests", blank=True, null=True
    )
    scheduled_for = models.DateTimeField(blank=True, null=True)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    # When set, completing the job bills the tenant for the actual cost.
    charge_to_tenant = models.BooleanField(default=False)
    invoice = models.ForeignKey(
        "billing.Invoice",
        on_delete=models.SET_NULL,
        related_name="maintenance_requests",
        blank=True,
        null=True,
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="maintenance_reported",
        blank=True,
        null=True,
    )
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status", "priority"]),
            models.Index(fields=["organization", "completed_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "reference"],
                name="unique_maintenance_reference_per_organization",
            ),
            models.CheckConstraint(
                condition=Q(estimated_cost__isnull=True) | Q(estimated_cost__gte=0),
                name="maintenance_estimate_not_negative",
            ),
            models.CheckConstraint(
                condition=Q(actual_cost__isnull=True) | Q(actual_cost__gte=0),
                name="maintenance_cost_not_negative",
            ),
        ]

    def __str__(self):
        return f"{self.reference} {self.title}"


class MaintenanceUpdate(TimeStampedModel):
    """The request's conversation: replies, internal notes and status changes."""

    class Kind(models.TextChoices):
        COMMENT = "comment", "Comment"
        STATUS = "status", "Status change"

    request = models.ForeignKey(
        MaintenanceRequest, on_delete=models.CASCADE, related_name="updates"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="maintenance_updates",
        blank=True,
        null=True,
    )
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.COMMENT)
    body = models.TextField()
    # Internal notes stay with the landlord's team; the tenant never sees them.
    is_internal = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.request.reference} · {self.get_kind_display()}"


class MaintenancePhoto(TimeStampedModel):
    request = models.ForeignKey(MaintenanceRequest, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to=maintenance_photo_path)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="maintenance_photos",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["created_at", "id"]
