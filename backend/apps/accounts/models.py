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
