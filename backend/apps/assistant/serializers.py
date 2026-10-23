from rest_framework import serializers

from apps.billing.serializers import InvoiceSerializer, RecordPaymentSerializer
from apps.leases.serializers import LeaseSerializer
from apps.maintenance.serializers import (
    MaintenanceRequestSerializer,
    MaintenanceUpdateSerializer,
    VendorSerializer,
)
from apps.properties.serializers import PropertySerializer, UnitSerializer
from apps.tenants.serializers import TenantSerializer


class AssistantPropertySerializer(PropertySerializer):
    class Meta(PropertySerializer.Meta):
        fields = [name for name in PropertySerializer.Meta.fields if name != "cover_image"]


class AssistantUnitSerializer(UnitSerializer):
    pass


class AssistantTenantSerializer(TenantSerializer):
    lease = None

    class Meta(TenantSerializer.Meta):
        fields = [name for name in TenantSerializer.Meta.fields if name != "lease"]


class AssistantDraftLeaseSerializer(LeaseSerializer):
    activate = None

    class Meta(LeaseSerializer.Meta):
        fields = [name for name in LeaseSerializer.Meta.fields if name != "activate"]

    def create(self, validated_data):
        validated_data["activate"] = False
        return super().create(validated_data)


class AssistantInvoiceSerializer(InvoiceSerializer):
    pass


class AssistantRecordPaymentSerializer(RecordPaymentSerializer):
    pass


class AssistantVendorSerializer(VendorSerializer):
    pass


class AssistantMaintenanceRequestSerializer(MaintenanceRequestSerializer):
    source = serializers.CharField(read_only=True)


class AssistantMaintenanceCommentSerializer(MaintenanceUpdateSerializer):
    pass
