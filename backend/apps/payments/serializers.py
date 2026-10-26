from decimal import Decimal

from rest_framework import serializers

from .models import Collection, Destination, Payout, Withdrawal
from .services import normalize_phone


class CheckoutSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    idempotency_key = serializers.UUIDField()
    channel = serializers.ChoiceField(choices=["mobile-money", "card"], default="card")
    phone = serializers.CharField(max_length=24, required=False)
    operator = serializers.ChoiceField(choices=["mtn", "airtel", "zamtel"], required=False)

    def validate(self, attrs):
        if attrs["channel"] == "mobile-money":
            if not attrs.get("phone") or not attrs.get("operator"):
                raise serializers.ValidationError("Enter your mobile-money number and network.")
            attrs["phone"] = normalize_phone(attrs["phone"])
        elif "phone" in attrs or "operator" in attrs:
            raise serializers.ValidationError("Card checkout does not accept mobile-money details.")
        return attrs


class DestinationApprovalSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=24)
    operator = serializers.ChoiceField(choices=["mtn", "airtel", "zamtel"])
    account_name = serializers.CharField(max_length=180)
    reason = serializers.CharField(min_length=10, max_length=500)

    def validate_phone(self, value):
        return normalize_phone(value)


class DestinationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id")
    account_suffix = serializers.SerializerMethodField()
    checked_with_lenco = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = [
            "id",
            "kind",
            "phone",
            "operator",
            "bank_name",
            "account_suffix",
            "account_name",
            "checked_with_lenco",
            "enabled",
            "created_at",
        ]

    def get_account_suffix(self, row):
        return (row.account_number or row.phone)[-4:]

    def get_checked_with_lenco(self, row):
        return bool(row.lookup_name)


class AccountDetailsSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=Destination.Kind.values, default="mobile-money")
    phone = serializers.CharField(max_length=24, required=False, allow_blank=True)
    operator = serializers.ChoiceField(
        choices=["mtn", "airtel", "zamtel"], required=False, allow_blank=True
    )
    bank_id = serializers.CharField(max_length=64, required=False, allow_blank=True)
    account_number = serializers.RegexField(
        r"^[0-9]{6,20}$",
        required=False,
        allow_blank=True,
        error_messages={"invalid": "Enter the account number using digits only."},
    )

    def validate(self, attrs):
        if attrs["kind"] == "bank-account":
            if not attrs.get("bank_id") or not attrs.get("account_number"):
                raise serializers.ValidationError("Choose the bank and enter the account number.")
            attrs["phone"] = attrs["operator"] = ""
        else:
            if not attrs.get("phone") or not attrs.get("operator"):
                raise serializers.ValidationError("Choose the network and enter the phone number.")
            attrs["phone"] = normalize_phone(attrs["phone"])
            attrs["bank_id"] = attrs["account_number"] = ""
        return attrs


class DestinationSetupSerializer(AccountDetailsSerializer):
    # Only used when Lenco cannot return the registered name (test bypass).
    account_name = serializers.CharField(
        min_length=2, max_length=180, required=False, allow_blank=True
    )
    confirm_details = serializers.BooleanField()
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)
    code = serializers.RegexField(r"^[0-9]{6}$", required=False, write_only=True)

    def validate_confirm_details(self, value):
        if not value:
            raise serializers.ValidationError("Confirm these receiving details before saving.")
        return value


class WithdrawalPreviewSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))


class WithdrawalRequestSerializer(WithdrawalPreviewSerializer):
    fee = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))
    idempotency_key = serializers.UUIDField()


class WithdrawalSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id")
    destination = DestinationSerializer(read_only=True)

    class Meta:
        model = Withdrawal
        fields = [
            "id",
            "reference",
            "amount",
            "fee_reserved",
            "fee",
            "fee_charged",
            "status",
            "issue",
            "destination",
            "created_at",
            "submitted_at",
            "confirmed_at",
        ]


class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = ["reference", "amount", "status", "fee", "issue", "updated_at"]


class CollectionSerializer(serializers.ModelSerializer):
    provider_status = serializers.CharField(source="provider_state.status", default=None)
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
            "channel",
            "provider_status",
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
