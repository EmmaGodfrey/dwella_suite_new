from django.contrib import admin

from .models import Property, Unit


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ["name", "organization", "property_type", "management_status", "town"]
    search_fields = ["name", "address", "town"]
    list_filter = ["organization", "property_type", "management_status", "is_active"]


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ["name", "property", "organization", "rent_amount", "occupancy_status"]
    search_fields = ["name", "property__name"]
    list_filter = ["organization", "occupancy_status", "is_active"]
