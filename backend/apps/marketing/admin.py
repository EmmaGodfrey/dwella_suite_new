from django.contrib import admin

from .models import BetaApplication


@admin.register(BetaApplication)
class BetaApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "phone",
        "email",
        "role",
        "units",
        "town",
        "status",
        "created_at",
    ]
    list_filter = ["status", "role", "units", "town"]
    search_fields = ["name", "phone", "email", "town"]
    readonly_fields = ["created_at", "updated_at"]
