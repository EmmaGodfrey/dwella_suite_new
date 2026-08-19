from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel, UUIDModel


class AuditEvent(UUIDModel, TimeStampedModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="audit_events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=120, db_index=True)
    resource_type = models.CharField(max_length=120, blank=True)
    resource_id = models.CharField(max_length=120, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    request_id = models.CharField(max_length=120, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.action
