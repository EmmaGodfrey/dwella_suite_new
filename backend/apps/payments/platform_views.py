"""Read-only platform transaction browsing. Never contacts a payment provider."""

from django.conf import settings
from django.db.models import OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.response import Response

from apps.common.permissions import IsPlatformSuperuser

from .models import Collection, Exchange, Payout, ProviderTransaction
from .serializers import CollectionSerializer
from .views import PrivateView


class TransactionFilters(serializers.Serializer):
    kind = serializers.ChoiceField(
        choices=["collections", "payouts", "ledger"], default="collections"
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
        statuses = (
            Collection.Status.values if attrs["kind"] == "collections" else Payout.Status.values
        )
        if attrs.get("status") and attrs["status"] not in (
            ["credit", "debit"] if attrs["kind"] == "ledger" else statuses
        ):
            raise serializers.ValidationError({"status": "Choose a valid status."})
        if attrs.get("payout_status") and attrs["payout_status"] not in Payout.Status.values:
            raise serializers.ValidationError({"payout_status": "Choose a valid payout status."})
        return attrs


class PlatformCollectionSerializer(CollectionSerializer):
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


class LedgerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    environment = serializers.CharField(source="account.environment")
    currency = serializers.CharField(source="account.currency")
    exchange_id = serializers.UUIDField(source="exchange.public_id")
    collection_id = serializers.UUIDField(read_only=True, allow_null=True)
    payout_collection_id = serializers.UUIDField(read_only=True, allow_null=True)

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
            rows = (
                ProviderTransaction.objects.select_related("account", "exchange")
                .defer("exchange__encrypted_payload")
                .annotate(
                    collection_id=Subquery(collections.values("public_id")[:1]),
                    payout_collection_id=Subquery(payouts.values("collection__public_id")[:1]),
                )
            )
            env_key, date_key = "account__environment", "posted_at"
            if filters.get("search"):
                rows = rows.filter(provider_id__icontains=filters["search"])
            if filters.get("status"):
                rows = rows.filter(kind=filters["status"])
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
                "api_configured": bool(settings.LENCO_PUBLIC_KEY and settings.LENCO_SECRET_KEY),
                "account_configured": bool(settings.LENCO_DEBIT_ACCOUNT_ID),
                "last_webhook_at": latest.order_by("-id")
                .values_list("created_at", flat=True)
                .first(),
            }
        )
