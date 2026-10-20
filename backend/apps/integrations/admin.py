from django.contrib import admin

from .models import FiscalReceipt, SmartInvoiceSettings


@admin.register(SmartInvoiceSettings)
class SmartInvoiceSettingsAdmin(admin.ModelAdmin):
    list_display = ("organization", "tpin", "branch_id", "enabled", "initialized_at")
    list_filter = ("enabled",)
    search_fields = ("organization__name", "tpin")
    readonly_fields = ("sdc_id", "mrc_no", "taxpayer_name", "initialized_at")


@admin.register(FiscalReceipt)
class FiscalReceiptAdmin(admin.ModelAdmin):
    list_display = ("invoice", "kind", "status", "invoice_number", "receipt_number", "issued_at")
    list_filter = ("status", "kind")
    search_fields = ("invoice__reference", "organization__name")
    readonly_fields = [field.name for field in FiscalReceipt._meta.fields]
