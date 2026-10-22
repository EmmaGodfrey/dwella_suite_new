from django.conf import settings
from django.db import models


class BetaApplication(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    class Source(models.TextChoices):
        WEBSITE = "website", "Website"
        ADMIN = "admin", "Added by Dwella"

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    role = models.CharField(max_length=50)
    units = models.CharField(max_length=50)
    town = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.WEBSITE)
    internal_notes = models.TextField(blank=True)
    # Countdown emails stop here; the beta-day access email is still sent.
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="beta_applications",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.phone})"


class BetaEmail(models.Model):
    """One row per sequence step delivered, so each step is sent at most once."""

    class Kind(models.TextChoices):
        WELCOME = "welcome", "Welcome"
        TWO_WEEKS = "two_weeks", "Two weeks to go"
        ONE_WEEK = "one_week", "One week to go"
        EVE = "eve", "Beta tomorrow"
        ACCESS = "access", "Sign-in details"

    application = models.ForeignKey(
        BetaApplication, on_delete=models.CASCADE, related_name="emails"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    sent_at = models.DateTimeField()

    class Meta:
        ordering = ["sent_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["application", "kind"], name="marketing_beta_email_once_per_step"
            )
        ]

    def __str__(self):
        return f"{self.get_kind_display()} → {self.application}"
