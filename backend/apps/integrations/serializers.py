import re

from rest_framework import serializers

from .models import FiscalReceipt, SmartInvoiceSettings
from .zra.codes import TAX_RATES, TaxCategory

DEVICE_FIELDS = ("tpin", "branch_id", "device_serial")


def tax_categories():
    return [
        {"value": value, "label": label, "rate": str(TAX_RATES[value])}
        for value, label in TaxCategory.choices
    ]


class SmartInvoiceSettingsSerializer(serializers.ModelSerializer):
    is_ready = serializers.BooleanField(read_only=True)

    class Meta:
        model = SmartInvoiceSettings
        fields = [
            "enabled",
            "is_ready",
            "tpin",
            "branch_id",
            "device_serial",
            "residential_tax_category",
            "commercial_tax_category",
            "taxpayer_name",
            "sdc_id",
            "mrc_no",
            "initialized_at",
            "updated_at",
        ]
        read_only_fields = ["taxpayer_name", "sdc_id", "mrc_no", "initialized_at", "updated_at"]

    def validate_tpin(self, value):
        value = value.strip()
        if not re.fullmatch(r"\d{10}", value):
            raise serializers.ValidationError("A TPIN is 10 digits.")
        return value

    def validate_branch_id(self, value):
        value = value.strip()
        if not re.fullmatch(r"\d{3}", value):
            raise serializers.ValidationError("A branch ID is 3 digits, for example 000.")
        return value

    def validate_device_serial(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Enter the device serial number from ZRA.")
        return value

    def validate(self, attrs):
        instance = self.instance
        connected = bool(instance and instance.initialized_at)
        if connected:
            changed = [
                name
                for name in DEVICE_FIELDS
                if name in attrs and attrs[name] != getattr(instance, name)
            ]
            if changed:
                raise serializers.ValidationError(
                    {name: ["This device is already connected to ZRA."] for name in changed}
                )
        if attrs.get("enabled") and not connected:
            raise serializers.ValidationError(
                {"enabled": ["Connect the device to ZRA before turning Smart Invoice on."]}
            )
        return attrs


class FiscalReceiptSerializer(serializers.ModelSerializer):
    tax_category = serializers.SerializerMethodField()
    tax_rate = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta:
        model = FiscalReceipt
        fields = [
            "kind",
            "status",
            "invoice_number",
            "original_invoice_number",
            "receipt_number",
            "total_receipt_number",
            "internal_data",
            "signature",
            "sdc_id",
            "mrc_no",
            "issued_at",
            "total",
            "tax_total",
            "tax_category",
            "tax_rate",
            "items",
            "error_message",
            "attempts",
            "created_at",
        ]
        read_only_fields = fields

    @staticmethod
    def _items(obj):
        return obj.request_payload.get("itemList") or []

    def get_tax_category(self, obj):
        items = self._items(obj)
        return items[0]["vatCatCd"] if items else None

    def get_tax_rate(self, obj):
        category = self.get_tax_category(obj)
        return str(TAX_RATES[category]) if category in TAX_RATES else None

    def get_items(self, obj):
        return [
            {
                "description": item["itemNm"],
                "amount": f"{item['totAmt']:.2f}",
                "tax": f"{item['vatAmt']:.2f}",
                "tax_category": item["vatCatCd"],
            }
            for item in self._items(obj)
        ]
