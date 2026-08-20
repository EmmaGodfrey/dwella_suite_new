from django.contrib import admin

from .models import IdentityVerification, PasswordResetRequest, TwoFactorDevice, UserProfile


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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_number", "job_title", "updated_at"]
    search_fields = ["user__email", "user__username", "phone_number", "job_title"]


@admin.register(IdentityVerification)
class IdentityVerificationAdmin(admin.ModelAdmin):
    list_display = ["user", "status", "legal_name", "document_type", "submitted_at", "reviewed_at"]
    list_filter = ["status", "document_type", "submitted_at"]
    search_fields = ["user__email", "legal_name", "document_number_last4"]
    readonly_fields = ["submitted_at", "created_at", "updated_at"]
