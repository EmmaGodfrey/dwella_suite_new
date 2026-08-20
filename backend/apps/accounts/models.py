from django.conf import settings
from django.db import models
from django.utils import timezone


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
