from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import OrganizationScopedModel


class NotificationPreferences(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    in_app_payment = models.BooleanField(default=True)
    in_app_payout = models.BooleanField(default=True)
    in_app_lease = models.BooleanField(default=True)
    in_app_maintenance = models.BooleanField(default=True)
    # What a tenant receives until they choose otherwise. Settings shows these same
    # defaults. WhatsApp stays off: business-initiated messages need explicit opt-in.
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    whatsapp_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification preferences for user {self.user_id}"


class ReminderPreferences(models.Model):
    organization = models.OneToOneField("organizations.Organization", on_delete=models.CASCADE)
    email_enabled = models.BooleanField(default=False)
    sms_enabled = models.BooleanField(default=False)
    whatsapp_enabled = models.BooleanField(default=False)
    before_due_days = models.PositiveSmallIntegerField(default=3)
    due_hour = models.PositiveSmallIntegerField(default=9)
    overdue_every_days = models.PositiveSmallIntegerField(default=3)
    overdue_repeats = models.PositiveSmallIntegerField(default=3)
    # Today's resumable reminder run: its local date and the last invoice handled.
    # A null run_after_id with today's run_date means today's run is finished.
    run_date = models.DateField(null=True, editable=False)
    run_after_id = models.BigIntegerField(null=True, editable=False)
    # When the scheduler should next look at this workspace. Null means "work it out".
    next_run_at = models.DateTimeField(null=True, editable=False)

    class Meta:
        indexes = [models.Index(fields=["next_run_at"], name="notifications_reminder_due")]

    def __str__(self):
        return f"Reminder preferences for workspace {self.organization_id}"


class MessagingSettings(models.Model):
    quiet_from = models.TimeField(default="20:00")
    quiet_until = models.TimeField(default="07:00")
    reminders_enabled = models.BooleanField(default=False)

    def __str__(self):
        return "Platform messaging settings"


class NotificationRead(models.Model):
    """Personal acknowledgement of a live portfolio alert."""

    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user", "key"], name="unique_notification_read"
            )
        ]

    def __str__(self):
        return f"{self.user_id}: {self.key}"


class MessageRequest(OrganizationScopedModel):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    channel = models.CharField(
        max_length=12, choices=[(c, c.title()) for c in ("email", "sms", "whatsapp")]
    )
    subject = models.CharField(max_length=160)
    body = models.TextField(max_length=2000)
    recipients = models.JSONField(default=list)
    expires_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True)
    source = models.CharField(max_length=16, default="manager")

    class Meta:
        indexes = [models.Index(fields=["organization", "created_at"])]


class MessageDelivery(OrganizationScopedModel):
    class Status(models.TextChoices):
        HELD = "held", "Held"
        QUEUED = "queued", "Queued"
        SENDING = "sending", "Sending"
        SENT = "sent", "Sent to email server"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REVIEW = "review", "Needs review"

    request = models.ForeignKey(MessageRequest, on_delete=models.PROTECT, null=True)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT)
    invoice = models.ForeignKey("billing.Invoice", on_delete=models.PROTECT, null=True)
    channel = models.CharField(max_length=12)
    recipient = models.CharField(max_length=254)
    subject = models.CharField(max_length=160)
    body = models.TextField()
    identity = models.CharField(max_length=140, unique=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.HELD)
    reason = models.CharField(max_length=80, blank=True)
    reminder_date = models.DateField(null=True)
    claimed_at = models.DateTimeField(null=True)
    available_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True)
    provider_id = models.CharField(max_length=160, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(
                fields=["channel", "claimed_at"],
                condition=models.Q(claimed_at__isnull=False),
                name="notifications_delivery_sent",
            ),
        ]
