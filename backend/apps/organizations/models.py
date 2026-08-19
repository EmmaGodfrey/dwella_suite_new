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

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.display_name or self.name


class OrganizationMembership(UUIDModel, TimeStampedModel, ActiveModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        STAFF = "staff", "Staff"
        VIEWER = "viewer", "Viewer"

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
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
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
