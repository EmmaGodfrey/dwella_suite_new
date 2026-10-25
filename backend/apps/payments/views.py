from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.common.permissions import CanViewPortfolio, IsPlatformSuperuser
from apps.common.workspaces import resolve_workspace
from apps.organizations.models import Organization
from apps.portal.access import IsPortalTenant, portal_context
from apps.portal.views import invoices

from .evidence import read_exchange
from .models import Collection, Destination, Exchange
from .serializers import (
    CheckoutSerializer,
    CollectionSerializer,
    DestinationApprovalSerializer,
    DestinationSerializer,
    TenantCollectionSerializer,
)
from .services import approve_destination, checkout_payload, start_checkout
from .webhooks import MAX_WEBHOOK, receive_webhook


class PaymentWriteThrottle(UserRateThrottle):
    scope = "payment_write"
    rate = "30/hour"


class WebhookThrottle(AnonRateThrottle):
    scope = "lenco_webhook"
    rate = "600/minute"


class PrivateView(APIView):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


class TenantCheckoutView(PrivateView):
    permission_classes = [IsPortalTenant]
    throttle_classes = [PaymentWriteThrottle]

    def post(self, request, public_id):
        invoice = get_object_or_404(invoices(portal_context(request)), public_id=public_id)
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = start_checkout(invoice=invoice, user=request.user, **serializer.validated_data)
        return Response(
            {
                "collection": TenantCollectionSerializer(row).data,
                "checkout": checkout_payload(row) if row.status == "pending" else None,
            }
        )


class TenantPaymentOptionsView(PrivateView):
    permission_classes = [IsPortalTenant]

    def get(self, request):
        from rest_framework.exceptions import PermissionDenied

        from apps.subscriptions.catalog import Feature
        from apps.subscriptions.services import require_feature

        org = portal_context(request).organization
        try:
            require_feature(org, Feature.ONLINE_PAYMENTS)
            entitled = True
        except PermissionDenied:
            entitled = False
        enabled = bool(
            entitled
            and settings.LENCO_PAYMENTS_ENABLED
            and settings.LENCO_PUBLIC_KEY
            and settings.LENCO_SECRET_KEY
            and settings.LENCO_DEBIT_ACCOUNT_ID
            and org.currency == "ZMW"
            and Destination.objects.filter(organization=org, enabled=True).exists()
        )
        return Response({"enabled": enabled, "currency": "ZMW"})


class TenantCollectionList(PrivateView, generics.ListAPIView):
    permission_classes = [IsPortalTenant]
    serializer_class = TenantCollectionSerializer

    def get_queryset(self):
        rows = Collection.objects.filter(invoice__in=invoices(portal_context(self.request)))
        invoice_id = self.request.query_params.get("invoice")
        if invoice_id:
            from uuid import UUID

            try:
                UUID(invoice_id)
            except ValueError:
                raise ValidationError("Invalid invoice ID.") from None
            rows = rows.filter(invoice__public_id=invoice_id)
        return rows.select_related("invoice", "payment")


class TenantCollectionDetail(PrivateView):
    permission_classes = [IsPortalTenant]
    throttle_classes = [PaymentWriteThrottle]

    def row(self, request, public_id):
        return get_object_or_404(
            Collection.objects.filter(invoice__in=invoices(portal_context(request))),
            public_id=public_id,
        )

    def get(self, request, public_id):
        return Response(TenantCollectionSerializer(self.row(request, public_id)).data)

    def post(self, request, public_id):
        row = self.row(request, public_id)
        # Queue verification; the callback is never evidence of payment.
        Collection.objects.filter(pk=row.pk).update(last_checked_at=None)
        return Response(TenantCollectionSerializer(row).data, status=202)


class ManagerCollectionList(PrivateView, generics.ListAPIView):
    permission_classes = [CanViewPortfolio]
    serializer_class = CollectionSerializer

    def get_queryset(self):
        rows = Collection.objects.filter(
            organization=resolve_workspace(self.request)
        ).select_related("invoice", "payment", "destination", "payout")
        invoice_id = self.request.query_params.get("invoice")
        if invoice_id:
            from uuid import UUID

            try:
                UUID(invoice_id)
            except ValueError:
                raise ValidationError("Invalid invoice ID.") from None
            rows = rows.filter(invoice__public_id=invoice_id)
        return rows


class ManagerDestinationView(PrivateView):
    permission_classes = [CanViewPortfolio]

    def get(self, request):
        row = Destination.objects.filter(
            organization=resolve_workspace(request), enabled=True
        ).first()
        return Response(
            {
                "destination": DestinationSerializer(row).data if row else None,
                "collection_enabled": settings.LENCO_PAYMENTS_ENABLED,
            }
        )


class PlatformDestinationView(PrivateView):
    permission_classes = [IsPlatformSuperuser]
    throttle_classes = [PaymentWriteThrottle]

    @transaction.atomic
    def post(self, request, public_id):
        organization = get_object_or_404(Organization, public_id=public_id, is_active=True)
        serializer = DestinationApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = approve_destination(
            organization=organization, user=request.user, **serializer.validated_data
        )
        record_event(
            request,
            "payment.destination_approved",
            row,
            organization,
            reason=serializer.validated_data["reason"],
            operator=row.operator,
            phone_suffix=row.phone[-4:],
        )
        return Response(DestinationSerializer(row).data, status=201)


class PlatformCollectionList(PrivateView, generics.ListAPIView):
    permission_classes = [IsPlatformSuperuser]
    serializer_class = CollectionSerializer
    queryset = Collection.objects.select_related("invoice", "payment", "destination", "payout")


class PlatformExchangeList(PrivateView, generics.ListAPIView):
    permission_classes = [IsPlatformSuperuser]

    def get(self, request, public_id):
        row = get_object_or_404(Collection, public_id=public_id)
        exchanges = Exchange.objects.filter(collection=row).order_by("-created_at")
        page = self.paginate_queryset(exchanges)
        return self.get_paginated_response(
            [
                {
                    "id": str(item.public_id),
                    "operation": item.operation,
                    "http_status": item.http_status,
                    "error": item.error,
                    "created_at": item.created_at,
                    "body_sha256": item.body_sha256,
                }
                for item in page
            ]
        )


class PlatformExchangeDetail(PrivateView):
    permission_classes = [IsPlatformSuperuser]

    def get(self, request, public_id):
        row = get_object_or_404(Exchange, public_id=public_id)
        record_event(
            request,
            "payment.evidence_viewed",
            row,
            row.collection.organization if row.collection_id else None,
        )
        return Response(read_exchange(row))


class WebhookView(PrivateView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [WebhookThrottle]

    def post(self, request):
        try:
            declared = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            raise ValidationError("Invalid content length.") from None
        if declared > MAX_WEBHOOK:
            raise ValidationError("Webhook exceeds the size limit.")
        receive_webhook(request.body, request.headers.get("X-Lenco-Signature", ""))
        return Response({"accepted": True})


class PlatformBalanceView(PrivateView):
    permission_classes = [IsPlatformSuperuser]

    def get(self, request):
        from decimal import Decimal

        from .models import BalanceSnapshot

        snapshot = (
            BalanceSnapshot.objects.filter(
                account__environment=settings.LENCO_ENVIRONMENT,
                account__account_id=settings.LENCO_DEBIT_ACCOUNT_ID,
            ).first()
            if settings.LENCO_DEBIT_ACCOUNT_ID
            else None
        )
        if snapshot is None:
            return Response({"status": "not_synced"})
        fields = [
            "status",
            "issue",
            "created_at",
            "available_balance",
            "ledger_balance",
            "expected_balance",
            "difference",
            "app_expected_balance",
            "app_difference",
            "credits_total",
            "debits_total",
            "transaction_count",
            "rent_collections_total",
            "rent_settled_total",
            "payouts_total",
            "payout_fees_total",
        ]
        values = {key: getattr(snapshot, key) for key in fields}
        return Response(
            {
                key: f"{value:.2f}" if isinstance(value, Decimal) else value
                for key, value in values.items()
            }
        )
