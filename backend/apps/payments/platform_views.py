"""Read-only platform transaction browsing. Never contacts a payment provider."""

from django.conf import settings
from django.db import transaction
from django.db.models import OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from apps.audit.runtime_settings import runtime_settings
from apps.common.permissions import IsPlatformSuperuser

from .models import Collection, Exchange, Payout, ProviderTransaction, Withdrawal
from .serializers import CollectionSerializer, WithdrawalSerializer
from .views import PrivateView


class TransactionFilters(serializers.Serializer):
    kind = serializers.ChoiceField(
        choices=["collections", "payouts", "withdrawals", "ledger"], default="collections"
    )
    search = serializers.CharField(max_length=150, required=False, allow_blank=True)
    status = serializers.CharField(max_length=20, required=False, allow_blank=True)
    payout_status = serializers.CharField(max_length=20, required=False, allow_blank=True)
    environment = serializers.ChoiceField(choices=["live", "sandbox", ""], required=False)
    workspace = serializers.UUIDField(required=False)
    from_date = serializers.DateField(required=False)
    until_date = serializers.DateField(required=False)

    def validate(self, attrs):
        if attrs.get("from_date") and attrs.get("until_date"):
            if attrs["from_date"] > attrs["until_date"]:
                raise serializers.ValidationError("End date must follow start date.")
        statuses = {
            "collections": Collection.Status.values,
            "withdrawals": Withdrawal.Status.values,
        }.get(attrs["kind"], Payout.Status.values)
        if attrs.get("status") and attrs["status"] not in (
            ["credit", "debit"] if attrs["kind"] == "ledger" else statuses
        ):
            raise serializers.ValidationError({"status": "Choose a valid status."})
        if attrs.get("payout_status") and attrs["payout_status"] not in Payout.Status.values:
            raise serializers.ValidationError({"payout_status": "Choose a valid payout status."})
        return attrs


class PlatformCollectionSerializer(CollectionSerializer):
    # Only platform superusers reach the views that use this.
    admin_only_fields = ()

    environment = serializers.CharField()
    workspace = serializers.CharField(source="organization.name")
    workspace_id = serializers.UUIDField(source="organization.public_id")
    invoice_reference = serializers.CharField(source="invoice.reference")

    class Meta(CollectionSerializer.Meta):
        fields = [
            *CollectionSerializer.Meta.fields,
            "environment",
            "workspace",
            "workspace_id",
            "invoice_reference",
        ]


class PlatformPayoutSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id")
    collection_id = serializers.UUIDField(source="collection.public_id")
    collection_reference = serializers.CharField(source="collection.reference")
    workspace = serializers.CharField(source="collection.organization.name")
    environment = serializers.CharField(source="collection.environment")
    currency = serializers.CharField(source="collection.currency")
    settled = serializers.BooleanField(source="collection.settled")

    class Meta:
        model = Payout
        fields = [
            "id",
            "reference",
            "collection_id",
            "collection_reference",
            "workspace",
            "environment",
            "currency",
            "amount",
            "fee",
            "settled",
            "status",
            "issue",
            "submitted_at",
            "confirmed_at",
            "created_at",
        ]


class PlatformWithdrawalSerializer(WithdrawalSerializer):
    workspace = serializers.CharField(source="organization.name")
    workspace_id = serializers.UUIDField(source="organization.public_id")
    environment = serializers.CharField()

    class Meta(WithdrawalSerializer.Meta):
        fields = [*WithdrawalSerializer.Meta.fields, "workspace", "workspace_id", "environment"]


class LedgerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    environment = serializers.CharField(source="account.environment")
    currency = serializers.CharField(source="account.currency")
    exchange_id = serializers.UUIDField(source="exchange.public_id")
    collection_id = serializers.UUIDField(read_only=True, allow_null=True)
    payout_collection_id = serializers.UUIDField(read_only=True, allow_null=True)
    withdrawal_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = ProviderTransaction
        fields = [
            "id",
            "provider_id",
            "kind",
            "amount",
            "posted_at",
            "environment",
            "currency",
            "exchange_id",
            "collection_id",
            "payout_collection_id",
            "withdrawal_id",
        ]


class PlatformTransactionsView(PrivateView, generics.ListAPIView):
    permission_classes = [IsPlatformSuperuser]

    def filters(self):
        if not hasattr(self, "validated_filters"):
            serializer = TransactionFilters(data=self.request.query_params)
            serializer.is_valid(raise_exception=True)
            self.validated_filters = serializer.validated_data
        return self.validated_filters

    def get_serializer_class(self):
        return {
            "collections": PlatformCollectionSerializer,
            "payouts": PlatformPayoutSerializer,
            "withdrawals": PlatformWithdrawalSerializer,
            "ledger": LedgerSerializer,
        }[self.filters()["kind"]]

    def get_queryset(self):
        filters = self.filters()
        kind = filters["kind"]
        if kind == "ledger":
            collections = Collection.objects.filter(
                provider_id=OuterRef("provider_id"), environment=OuterRef("account__environment")
            )
            payouts = Payout.objects.filter(
                provider_id=OuterRef("provider_id"),
                collection__environment=OuterRef("account__environment"),
            )
            withdrawals = Withdrawal.objects.filter(
                provider_id=OuterRef("provider_id"), environment=OuterRef("account__environment")
            )
            rows = (
                ProviderTransaction.objects.select_related("account", "exchange")
                .defer("exchange__encrypted_payload")
                .annotate(
                    collection_id=Subquery(collections.values("public_id")[:1]),
                    payout_collection_id=Subquery(payouts.values("collection__public_id")[:1]),
                    withdrawal_id=Subquery(withdrawals.values("public_id")[:1]),
                )
            )
            env_key, date_key = "account__environment", "posted_at"
            if filters.get("search"):
                rows = rows.filter(provider_id__icontains=filters["search"])
            if filters.get("status"):
                rows = rows.filter(kind=filters["status"])
        elif kind == "withdrawals":
            rows = Withdrawal.objects.select_related("organization", "destination")
            env_key, date_key = "environment", "created_at"
            if filters.get("search"):
                rows = rows.filter(
                    Q(reference__icontains=filters["search"])
                    | Q(organization__name__icontains=filters["search"])
                )
            if filters.get("workspace"):
                rows = rows.filter(organization__public_id=filters["workspace"])
            if filters.get("status"):
                rows = rows.filter(status=filters["status"])
        else:
            prefix = "collection__" if kind == "payouts" else ""
            if kind == "payouts":
                rows = Payout.objects.select_related("collection__organization")
            else:
                rows = Collection.objects.select_related(
                    "organization", "invoice", "payment", "destination", "payout"
                )
            env_key, date_key = f"{prefix}environment", "created_at"
            if filters.get("search"):
                rows = rows.filter(
                    Q(reference__icontains=filters["search"])
                    | Q(**{f"{prefix}invoice__reference__icontains": filters["search"]})
                    | Q(**{f"{prefix}organization__name__icontains": filters["search"]})
                )
            if filters.get("workspace"):
                rows = rows.filter(**{f"{prefix}organization__public_id": filters["workspace"]})
            if filters.get("status"):
                rows = rows.filter(status=filters["status"])
            if kind == "collections" and filters.get("payout_status"):
                rows = rows.filter(payout__status=filters["payout_status"])
        if filters.get("environment"):
            rows = rows.filter(**{env_key: filters["environment"]})
        for param, suffix in [("from_date", "gte"), ("until_date", "lte")]:
            if filters.get(param):
                rows = rows.filter(**{f"{date_key}__date__{suffix}": filters[param]})
        return rows.order_by(f"-{date_key}", "-pk")


class PlatformCollectionDetail(PrivateView):
    permission_classes = [IsPlatformSuperuser]

    def get(self, request, public_id):
        row = get_object_or_404(
            Collection.objects.select_related(
                "organization", "invoice", "payment", "destination", "payout"
            ),
            public_id=public_id,
        )
        return Response(PlatformCollectionSerializer(row).data)


class PlatformWithdrawalDetail(PrivateView):
    permission_classes = [IsPlatformSuperuser]

    def get(self, request, public_id):
        row = get_object_or_404(
            Withdrawal.objects.select_related("organization", "destination"), public_id=public_id
        )
        return Response(PlatformWithdrawalSerializer(row).data)


class PlatformPaymentConfiguration(PrivateView):
    permission_classes = [IsPlatformSuperuser]

    def get(self, request):
        latest = Exchange.objects.filter(
            environment=settings.LENCO_ENVIRONMENT, operation="webhook"
        )
        return Response(
            {
                "gateway": "Lenco by Broadpay",
                "environment": settings.LENCO_ENVIRONMENT,
                "collections_enabled": settings.LENCO_PAYMENTS_ENABLED,
                "payouts_enabled": settings.LENCO_PAYOUTS_ENABLED,
                "card_enabled": runtime_settings()["payments_card_enabled"],
                "mobile_money_enabled": runtime_settings()["payments_mobile_money_enabled"],
                "api_configured": bool(settings.LENCO_PUBLIC_KEY and settings.LENCO_SECRET_KEY),
                "account_configured": bool(settings.LENCO_DEBIT_ACCOUNT_ID),
                "last_webhook_at": latest.order_by("-id")
                .values_list("created_at", flat=True)
                .first(),
            }
        )


class PaymentSwitchThrottle(UserRateThrottle):
    scope = "payment_switch"
    rate = "10/hour"


class PaymentSwitchSerializer(serializers.Serializer):
    card = serializers.BooleanField(required=False)
    mobile_money = serializers.BooleanField(required=False)
    password = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)
    code = serializers.RegexField(r"^[0-9]{6}$", write_only=True)

    def validate(self, attrs):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError("Unsupported fields.")
        if not {"card", "mobile_money"} & set(attrs):
            raise serializers.ValidationError("Choose card or mobile money to change.")
        return attrs


@method_decorator(sensitive_post_parameters("password", "code"), name="dispatch")
class PlatformPaymentSwitches(PrivateView):
    """Turn online card / mobile-money collection on or off. Needs password + fresh code."""

    permission_classes = [IsPlatformSuperuser]
    throttle_classes = [PaymentSwitchThrottle]

    def post(self, request):
        from apps.audit.models import PlatformSettings
        from apps.audit.provider_credentials import verify_step_up
        from apps.audit.services import record_event

        serializer = PaymentSwitchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            verify_step_up(request, password=data["password"], code=data["code"])
            PlatformSettings.objects.get_or_create(pk=1)
            instance = PlatformSettings.objects.select_for_update().get(pk=1)
            changes = {}
            if "card" in data:
                changes["payments_card_enabled"] = data["card"]
            if "mobile_money" in data:
                changes["payments_mobile_money_enabled"] = data["mobile_money"]
            instance.runtime_config = {**instance.runtime_config, **changes}
            instance.save(update_fields=["runtime_config"])
            record_event(
                request, "platform.payment_methods_switched", instance, fields=sorted(changes)
            )
        config = runtime_settings(instance=instance)
        return Response(
            {
                "card": config["payments_card_enabled"],
                "mobile_money": config["payments_mobile_money_enabled"],
            }
        )
