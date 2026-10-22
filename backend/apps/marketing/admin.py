from django.contrib import admin

from .models import BetaApplication, BetaEmail


class BetaEmailInline(admin.TabularInline):
    model = BetaEmail
    extra = 0
    readonly_fields = ["kind", "sent_at"]
    can_delete = False


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
        "source",
        "created_at",
    ]
    list_filter = ["status", "source", "role", "units", "town"]
    search_fields = ["name", "phone", "email", "town"]
    readonly_fields = ["account", "unsubscribed_at", "created_at", "updated_at"]
    inlines = [BetaEmailInline]
