from decimal import Decimal

from rest_framework import serializers

from .models import Collection, Destination, Payout
from .services import normalize_phone


class CheckoutSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    idempotency_key = serializers.UUIDField()


class DestinationApprovalSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=24)
    operator = serializers.ChoiceField(choices=["mtn", "airtel", "zamtel"])
    account_name = serializers.CharField(max_length=180)
    reason = serializers.CharField(min_length=10, max_length=500)

    def validate_phone(self, value):
        return normalize_phone(value)


class DestinationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id")

    class Meta:
        model = Destination
        fields = ["id", "phone", "operator", "account_name", "enabled", "created_at"]


class DestinationSetupSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=24)
    operator = serializers.ChoiceField(choices=["mtn", "airtel", "zamtel"])
    account_name = serializers.CharField(min_length=2, max_length=180)
    confirm_details = serializers.BooleanField()

    def validate_phone(self, value):
        return normalize_phone(value)

    def validate_confirm_details(self, value):
        if not value:
            raise serializers.ValidationError("Confirm these receiving details before saving.")
        return value


class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = ["reference", "amount", "status", "fee", "issue", "updated_at"]


class CollectionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id")
    invoice_id = serializers.UUIDField(source="invoice.public_id")
    receipt_number = serializers.CharField(source="payment.receipt_number", default=None)
    payment_id = serializers.UUIDField(source="payment.public_id", default=None)
    payout = PayoutSerializer(read_only=True)
    destination = DestinationSerializer(read_only=True)

    class Meta:
        model = Collection
        fields = [
            "id",
            "reference",
            "invoice_id",
            "amount",
            "currency",
            "status",
            "fee",
            "settled",
            "settled_amount",
            "issue",
            "receipt_number",
            "payment_id",
            "payout",
            "destination",
            "created_at",
            "updated_at",
        ]


class TenantCollectionSerializer(CollectionSerializer):
    class Meta(CollectionSerializer.Meta):
        fields = [
            key
            for key in CollectionSerializer.Meta.fields
            if key not in {"destination", "payout", "fee", "settled_amount", "issue"}
        ]
