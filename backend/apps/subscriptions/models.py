from django.db import models

from apps.common.models import TimeStampedModel, UUIDModel


class WorkspaceAccessPolicy(UUIDModel, TimeStampedModel):
    """Grants/capacity only; a future billing integration can populate this policy."""

    organization = models.OneToOneField(
        "organizations.Organization", on_delete=models.CASCADE, related_name="access_policy"
    )
    feature_overrides = models.JSONField(default=dict)
    limits = models.JSONField(default=dict)

    def __str__(self):
        return f"Access policy for {self.organization_id}"
