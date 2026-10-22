from django.contrib import admin

from .models import AuditEvent, SupportSession


@admin.register(SupportSession)
class SupportSessionAdmin(admin.ModelAdmin):
    list_display = ["admin", "organization", "reason", "started_at", "ended_at", "expires_at"]
    readonly_fields = [field.name for field in SupportSession._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ["action", "organization", "actor", "resource_type", "created_at"]
    search_fields = ["action", "resource_type", "resource_id", "request_id"]
    list_filter = ["action", "resource_type", "created_at"]
    readonly_fields = [field.name for field in AuditEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
