from django.conf import settings
from django.db import models

from apps.common.models import ActiveModel, TimeStampedModel, UUIDModel


class Organization(UUIDModel, TimeStampedModel, ActiveModel):
    name = models.CharField(max_length=180, unique=True)
    display_name = models.CharField(max_length=180, blank=True)
    logo = models.ImageField(upload_to="organizations/logos/", blank=True, null=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    town = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=80, default="Zambia")
    currency = models.CharField(max_length=3, default="ZMW")
    timezone = models.CharField(max_length=80, default="Africa/Lusaka")
    # Rent invoices go out automatically this many days before each lease's due
    # day. Managers can still issue them by hand at any time.
    auto_invoice = models.BooleanField(default=True)
    invoice_lead_days = models.PositiveSmallIntegerField(default=7)
    # Empty means every connected property manager gets the WhatsApp review message.
    proof_reviewer = models.ForeignKey(
        "organizations.OrganizationMembership",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    # Property managers may cover a teammate's properties for a limited time.
    # Every covered change is recorded; an admin can switch this off.
    allow_teammate_cover = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.display_name or self.name


class OrganizationMembership(UUIDModel, TimeStampedModel, ActiveModel):
    class Role(models.TextChoices):
        # Stored key kept from the first release. A property admin oversees the
        # whole workspace; a property manager works on assigned properties only.
        LANDLORD = "landlord", "Property admin"
        MANAGER = "manager", "Property manager"
        TENANT = "tenant", "Tenant"

    MANAGEMENT_ROLES = (Role.LANDLORD, Role.MANAGER)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="organization_invitations_sent",
    )

    class Meta:
        ordering = ["organization__name", "user__email"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="unique_organization_membership",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.organization} ({self.role})"


class PropertyAssignment(UUIDModel, TimeStampedModel):
    """A property manager's access to one whole property."""

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="property_assignments"
    )
    membership = models.ForeignKey(
        OrganizationMembership, on_delete=models.CASCADE, related_name="property_assignments"
    )
    property = models.ForeignKey(
        "properties.Property", on_delete=models.CASCADE, related_name="manager_assignments"
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["membership", "property"], name="unique_property_assignment"
            )
        ]

    def __str__(self):
        return f"{self.membership_id} -> {self.property_id}"


class TeamInvitation(UUIDModel, TimeStampedModel):
    """An emailed, single-use invitation to manage a workspace."""

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="team_invitations"
    )
    email = models.EmailField()
    full_name = models.CharField(max_length=180, blank=True)
    role = models.CharField(max_length=20, choices=OrganizationMembership.Role.choices)
    properties = models.ManyToManyField("properties.Property", blank=True, related_name="+")
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    accepted_at = models.DateTimeField(blank=True, null=True)
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="+"
    )
    revoked_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["organization", "email"])]

    def __str__(self):
        return f"{self.email} ({self.role})"


class CoverSession(UUIDModel, TimeStampedModel):
    """A property manager working on a teammate's properties for a limited time.

    The covering manager keeps their own identity on everything they record;
    each change made through the cover is written to the audit trail.
    """

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="cover_sessions"
    )
    manager = models.ForeignKey(
        OrganizationMembership, on_delete=models.CASCADE, related_name="cover_sessions"
    )
    covering_for = models.ForeignKey(
        OrganizationMembership, on_delete=models.CASCADE, related_name="covered_sessions"
    )
    reason = models.CharField(max_length=300)
    expires_at = models.DateTimeField()
    ended_at = models.DateTimeField(blank=True, null=True)
    ended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["manager", "ended_at", "expires_at"])]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(manager=models.F("covering_for")),
                name="cover_session_not_self",
            ),
            # One live cover per manager; expiry is checked when it is read.
            models.UniqueConstraint(
                fields=["manager"],
                condition=models.Q(ended_at__isnull=True),
                name="one_open_cover_per_manager",
            ),
        ]

    def __str__(self):
        return f"{self.manager_id} covering {self.covering_for_id}"
