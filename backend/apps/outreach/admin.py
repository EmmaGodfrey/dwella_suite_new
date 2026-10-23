from django.contrib import admin

from .models import (
    Contact,
    Enrollment,
    OutreachMessage,
    OutreachSettings,
    Sequence,
    Suppression,
    Template,
)


@admin.register(
    Contact, Enrollment, OutreachMessage, OutreachSettings, Sequence, Suppression, Template
)
class OutreachReadOnlyAdmin(admin.ModelAdmin):
    """All writes go through the audited platform API; suppressions cannot be removed."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
