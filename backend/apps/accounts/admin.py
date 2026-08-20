from django.contrib import admin

from .models import PasswordResetRequest, TwoFactorDevice


@admin.register(TwoFactorDevice)
class TwoFactorDeviceAdmin(admin.ModelAdmin):
    list_display = ["user", "is_confirmed", "created_at", "confirmed_at"]
    list_filter = ["is_confirmed", "created_at"]
    search_fields = ["user__email", "user__username"]


@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ["email", "ip_address", "created_at"]
    search_fields = ["email", "ip_address"]
    readonly_fields = ["email", "ip_address", "user_agent", "created_at"]
