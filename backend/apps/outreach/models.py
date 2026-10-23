from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from apps.common.models import TimeStampedModel, UUIDModel

SEGMENTS = [
    (s, s.replace("_", " ").title())
    for s in (
        "influencer",
        "agent",
        "property_manager",
        "landlord",
        "partner",
        "other",
    )
]
PLATFORMS = [
    (s, s.title())
    for s in (
        "tiktok",
        "instagram",
        "facebook",
        "linkedin",
        "website",
        "referral",
        "other",
    )
]
CONTACT_STATUSES = [
    (s, s.replace("_", " ").title())
    for s in (
        "new",
        "queued",
        "contacted",
        "replied",
        "interested",
        "partner",
        "not_interested",
        "do_not_contact",
        "bounced",
    )
]
LIVE_ENROLLMENTS = ("pending_review", "scheduled", "active", "paused")


class Contact(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=150)
    first_name = models.CharField(max_length=80, blank=True)
    salutation = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    whatsapp = models.CharField(max_length=32, blank=True)
    organization = models.CharField(max_length=150, blank=True)
    title = models.CharField(max_length=150, blank=True)
    segment = models.CharField(max_length=30, choices=SEGMENTS, default="other")
    platform = models.CharField(max_length=20, choices=PLATFORMS, default="other")
    handle = models.CharField(max_length=100, blank=True)
    profile_url = models.URLField(blank=True)
    audience_size = models.PositiveIntegerField(null=True, blank=True)
    town = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True, max_length=5000)
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=30, choices=CONTACT_STATUSES, default="new")
    source = models.CharField(max_length=500)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    beta_application = models.ForeignKey(
        "marketing.BetaApplication",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    last_contacted_at = models.DateTimeField(null=True, blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "pk"]
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                condition=~Q(email=""),
                name="outreach_contact_email_unique",
            )
        ]

    def __str__(self):
        return str(self.public_id)


class Template(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    segment = models.CharField(max_length=30, choices=SEGMENTS, default="other")
    subject = models.CharField(max_length=250)
    body = models.TextField(max_length=10000)
    whatsapp_body = models.TextField(max_length=4000, blank=True)
    is_follow_up = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["name"]


class Sequence(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    description = models.CharField(max_length=1000, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]


class SequenceStep(models.Model):
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, related_name="steps")
    template = models.ForeignKey(Template, on_delete=models.PROTECT)
    order = models.PositiveSmallIntegerField()
    wait_days = models.PositiveSmallIntegerField(default=0)
    only_if_no_reply = models.BooleanField(default=True, editable=False)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["sequence", "order"], name="outreach_step_order_unique"
            ),
            models.CheckConstraint(condition=Q(only_if_no_reply=True), name="outreach_reply_stop"),
        ]

    def __str__(self):
        return f"{self.sequence_id}:{self.order}"


class Enrollment(UUIDModel, TimeStampedModel):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="enrollments")
    sequence = models.ForeignKey(Sequence, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=30,
        default="pending_review",
        choices=[
            (s, s.replace("_", " ").title())
            for s in (
                *LIVE_ENROLLMENTS,
                "completed",
                "stopped_reply",
                "stopped_optout",
                "stopped_bounce",
                "cancelled",
            )
        ],
    )
    next_step = models.PositiveSmallIntegerField(default=0)
    next_send_at = models.DateTimeField(null=True, blank=True)
    personal_line = models.CharField(max_length=1000, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["contact"],
                condition=Q(status__in=LIVE_ENROLLMENTS),
                name="outreach_one_live_enrollment",
            )
        ]


class OutreachMessage(UUIDModel, TimeStampedModel):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="messages")
    step = models.PositiveSmallIntegerField()
    wait_days = models.PositiveSmallIntegerField(default=0)
    subject = models.CharField(max_length=250)
    body = models.TextField()
    recipient = models.EmailField()
    message_id = models.CharField(max_length=250, unique=True)
    status = models.CharField(
        max_length=20,
        default="pending",
        choices=[(s, s.title()) for s in ("pending", "sent", "failed", "bounced")],
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    error = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-created_at", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["enrollment", "step"],
                name="outreach_message_once_per_step",
            )
        ]


class Suppression(TimeStampedModel):
    email = models.EmailField(unique=True)
    reason = models.CharField(
        max_length=20,
        choices=[(s, s.title()) for s in ("unsubscribed", "bounced", "manual", "complaint")],
    )

    class Meta:
        constraints = [models.UniqueConstraint(Lower("email"), name="outreach_suppression_unique")]

    def __str__(self):
        return str(self.pk)


class OutreachSettings(TimeStampedModel):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    sender_name = models.CharField(max_length=150, blank=True)
    sender_first_name = models.CharField(max_length=80, blank=True)
    signature = models.TextField(max_length=2000, blank=True)
    signature_short = models.CharField(max_length=500, blank=True)
    offer = models.CharField(max_length=2000, blank=True)
    daily_cap = models.PositiveSmallIntegerField(default=10)
    send_from_hour = models.PositiveSmallIntegerField(default=8)
    send_until_hour = models.PositiveSmallIntegerField(default=17)
    paused = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(id=1), name="outreach_settings_singleton")
        ]


class ImportReceipt(models.Model):
    digest = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.pk)
