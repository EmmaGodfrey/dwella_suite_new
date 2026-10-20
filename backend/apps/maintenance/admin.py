from django.contrib import admin

from .models import MaintenancePhoto, MaintenanceRequest, MaintenanceUpdate, Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "trade", "phone_number", "organization", "is_active")
    search_fields = ("name", "trade", "organization__name")


class MaintenanceUpdateInline(admin.TabularInline):
    model = MaintenanceUpdate
    extra = 0


class MaintenancePhotoInline(admin.TabularInline):
    model = MaintenancePhoto
    extra = 0


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ("reference", "title", "property", "priority", "status", "organization")
    list_filter = ("status", "priority", "category")
    search_fields = ("reference", "title", "organization__name")
    inlines = [MaintenanceUpdateInline, MaintenancePhotoInline]
