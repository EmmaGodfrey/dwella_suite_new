from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel, UUIDModel


class AccountAccessState(TimeStampedModel):
    tenant_access_removed = models.BooleanField(default=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="account_access_state"
    )
    requires_verification = models.BooleanField(default=False)
    verified_email = models.EmailField(blank=True)
    verified_at = models.DateTimeField(null=True)

    def __str__(self):
        return f"Account access for {self.user_id}"


class EmailVerificationLink(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_verification_links"
    )
    email = models.EmailField()
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True)
    revoked_at = models.DateTimeField(null=True)

    def __str__(self):
        return f"Email verification {self.public_id}"


class TenantInvitation(UUIDModel, TimeStampedModel):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="portal_invitations"
    )
    email = models.EmailField()
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)
    accepted_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tenant_invitations_created",
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tenant_invitations_accepted",
        null=True,
    )

    def __str__(self):
        return f"Tenant invitation {self.public_id}"


class GuidedTourState(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE)
    tour_key = models.CharField(max_length=48)
    status = models.CharField(
        max_length=16,
        default="not_started",
        choices=[
            (key, key.replace("_", " ").title())
            for key in ["not_started", "in_progress", "paused", "skipped", "completed"]
        ],
    )
    completed_steps = models.JSONField(default=list)
    current_step = models.CharField(max_length=64, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "organization", "tour_key"], name="unique_user_workspace_tour"
            )
        ]

    def __str__(self):
        return f"{self.tour_key} for {self.user_id}"


class TwoFactorDevice(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="two_factor_device",
    )
    secret = models.CharField(max_length=64)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"2FA device for {self.user}"

    def mark_confirmed(self):
        self.is_confirmed = True
        self.confirmed_at = timezone.now()
        self.save(update_fields=["is_confirmed", "confirmed_at"])


class PasswordResetRequest(models.Model):
    email = models.EmailField(db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Password reset request for {self.email}"


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone_number = models.CharField(max_length=32, blank=True)
    job_title = models.CharField(max_length=120, blank=True)
    avatar = models.ImageField(upload_to="profiles/avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user}"


class IdentityVerification(models.Model):
    class Status(models.TextChoices):
        NOT_SUBMITTED = "not_submitted", "Not Submitted"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class DocumentType(models.TextChoices):
        NRC = "nrc", "NRC"
        PASSPORT = "passport", "Passport"
        DRIVERS_LICENSE = "drivers_license", "Driver's License"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="identity_verification",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_SUBMITTED,
        db_index=True,
    )
    legal_name = models.CharField(max_length=150, blank=True)
    document_type = models.CharField(max_length=32, choices=DocumentType.choices, blank=True)
    document_number_last4 = models.CharField(max_length=4, blank=True)
    document_image = models.ImageField(
        upload_to="profiles/verification_documents/",
        blank=True,
        null=True,
    )
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Identity verification for {self.user}"


class HandyActionExecution(models.Model):
    """Durable replay protection for an approved assistant action."""

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="handy_action_executions",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="handy_action_executions",
    )
    idempotency_key = models.CharField(max_length=160)
    operation = models.CharField(max_length=120)
    payload_hash = models.CharField(max_length=64)
    response_status = models.PositiveSmallIntegerField(default=201)
    response_data = models.JSONField(default=dict)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "actor", "operation", "idempotency_key"],
                name="unique_handy_action_execution",
            )
        ]
        indexes = [models.Index(fields=["organization", "created_at"])]

    def __str__(self):
        return f"{self.operation} by {self.actor_id}"
