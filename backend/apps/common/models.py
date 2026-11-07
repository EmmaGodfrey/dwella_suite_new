import uuid

from django.db import models

from .managers import ActiveManager, OrganizationScopedManager


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True


class ActiveModel(models.Model):
    is_active = models.BooleanField(default=True, db_index=True)

    objects = ActiveManager()

    class Meta:
        abstract = True


class OrganizationScopedModel(UUIDModel, TimeStampedModel, ActiveModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    objects = OrganizationScopedManager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["organization", "created_at"]),
        ]


class EmailRoutingLock(models.Model):
    """One short lock shared by every application email sender."""

    id = models.PositiveSmallIntegerField(primary_key=True, default=1)

    def __str__(self):
        return "Shared email routing lock"


class EmailUsageBucket(models.Model):
    provider = models.CharField(max_length=12)
    hour = models.DateTimeField()
    recipients = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "hour"], name="email_usage_hour")
        ]
        indexes = [models.Index(fields=["hour"], name="email_usage_retention")]

    def __str__(self):
        return f"{self.provider}: {self.hour}"
