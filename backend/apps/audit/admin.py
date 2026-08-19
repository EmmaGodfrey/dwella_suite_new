from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ["action", "organization", "actor", "resource_type", "created_at"]
    search_fields = ["action", "resource_type", "resource_id", "request_id"]
    list_filter = ["action", "resource_type", "created_at"]
