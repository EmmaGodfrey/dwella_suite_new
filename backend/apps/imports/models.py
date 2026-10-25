from django.conf import settings
from django.db import models

from apps.common.models import OrganizationScopedModel


class PortfolioImport(OrganizationScopedModel):
    """One confirmed bulk import. The digest stops a preview being applied twice."""

    class Kind(models.TextChoices):
        UNITS = "units", "Units"
        TENANTS = "tenants", "Tenants"

    kind = models.CharField(max_length=12, choices=Kind.choices)
    digest = models.CharField(max_length=64)
    created_count = models.PositiveIntegerField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "digest"], name="unique_import_preview_per_organization"
            )
        ]

    def __str__(self):
        return f"{self.get_kind_display()} import · {self.created_count}"
