from django.contrib import admin

from .models import Organization, OrganizationMembership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "display_name", "town", "country", "is_active"]
    search_fields = ["name", "display_name", "email", "phone_number"]
    list_filter = ["country", "is_active"]


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ["organization", "user", "role", "is_active"]
    search_fields = ["organization__name", "user__email", "user__username"]
    list_filter = ["role", "is_active"]
