from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.common.permissions import CanManageOrganization, CanViewPortfolio, IsPlatformSuperuser
from apps.common.workspaces import resolve_workspace
from apps.organizations.models import Organization, OrganizationMembership
from apps.portal.access import IsPortalTenant, portal_context
from apps.portal.views import invoices

from .evidence import read_exchange
from .models import Collection, Destination, Exchange, Withdrawal
from .serializers import (
    AccountDetailsSerializer,
    CheckoutSerializer,
    CollectionSerializer,
    DestinationApprovalSerializer,
    DestinationSerializer,
    DestinationSetupSerializer,
    TenantCollectionSerializer,
    WithdrawalPreviewSerializer,
    WithdrawalRequestSerializer,
    WithdrawalSerializer,
)
from .services import approve_destination, checkout_payload, start_checkout, submit_mobile_money
from .webhooks import MAX_WEBHOOK, receive_webhook
from .withdrawals import (
    AccountNotFound,
    balance,
    banks,
    cancel_withdrawal,
    current_destination,
    largest_withdrawal,
    look_up_account,
    quote,
    request_withdrawal,
    withdrawals_enabled,
)


class PaymentWriteThrottle(UserRateThrottle):
    scope = "payment_write"
    rate = "30/hour"


class CanSetReceivingDetails(CanManageOrganization):
    message = "Sign in as the property manager to set receiving details."

    def has_permission(self, request, view):
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return False
        return super().has_permission(request, view)


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
        if row.channel == "mobile-money":
            row = submit_mobile_money(row)
        return Response(
            {
                "collection": TenantCollectionSerializer(row).data,
                "checkout": checkout_payload(row)
                if row.status == "pending" and row.channel != "mobile-money"
                else None,
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
        # Bring the next check forward; the callback is never evidence of
        # payment. Finished rows have nothing left to check.
        Collection.objects.filter(pk=row.pk).filter(
            Q(status__in=["pending", "expired"]) | Q(status="successful", settled=False)
        ).update(next_check_at=timezone.now())
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


def landlord_workspace(request, *, lock=False):
    """The workspace an active property manager acts for; staff never act here."""
    if request.user.is_staff or request.user.is_superuser:
        raise PermissionDenied("Sign in as the property manager to manage withdrawals.")
    organization = resolve_workspace(request)
    if lock:
        organization = Organization.objects.select_for_update().get(pk=organization.pk)
    if not organization.is_active or organization.currency != "ZMW":
        raise ValidationError("Withdrawals need an active ZMW workspace.")
    if not OrganizationMembership.objects.filter(
        organization=organization,
        user=request.user,
        user__is_active=True,
        is_active=True,
        role="landlord",
    ).exists():
        raise PermissionDenied("Active property manager access is required.")
    return organization


def confirm_identity(user, data):
    """Changing where rent goes needs the password, and the code if 2FA is on."""
    from apps.accounts.models import TwoFactorDevice
    from apps.accounts.security import verify_totp

    device = TwoFactorDevice.objects.filter(user=user, is_confirmed=True).first()
    if not user.check_password(data["password"]):
        raise ValidationError({"password": "Check your password."})
    if device and not (data.get("code") and verify_totp(device.secret, data["code"])):
        raise ValidationError({"code": "Enter the code from your authenticator app."})


def lookup_bypass_allowed():
    return settings.APP_ENVIRONMENT == "test" and settings.LENCO_ALLOW_UNVERIFIED_DESTINATIONS


def bank_name(bank_id):
    match = next((bank for bank in banks() if bank["id"] == bank_id), None)
    if match is None:
        raise ValidationError({"bank_id": "Choose a bank from the list."})
    return match["name"]


def notify_destination_change(user, row):
    from apps.accounts.account_mail import send_account_mail

    if not user.email:
        return
    where = (
        f"{row.bank_name} account ending {row.account_number[-4:]}"
        if row.kind == "bank-account"
        else f"{row.operator.upper()} mobile money ending {row.phone[-4:]}"
    )
    send_account_mail(
        "Your Dwella receiving account changed",
        f"Withdrawals from {row.organization.name} will now go to {where} "
        f"({row.account_name}).\n\nIf you did not make this change, sign in, change your "
        "password and contact Dwella support straight away.",
        user.email,
    )


class ManagerDestinationView(PrivateView):
    permission_classes = [CanViewPortfolio]

    def get_throttles(self):
        return (
            [PaymentWriteThrottle()] if self.request.method == "POST" else super().get_throttles()
        )

    def get_permissions(self):
        classes = (
            [CanSetReceivingDetails] if self.request.method == "POST" else self.permission_classes
        )
        return [permission() for permission in classes]

    def get(self, request):
        row = current_destination(resolve_workspace(request))
        return Response(
            {
                "destination": DestinationSerializer(row).data if row else None,
                "collection_enabled": settings.LENCO_PAYMENTS_ENABLED,
                "self_service_enabled": bool(settings.LENCO_SECRET_KEY),
                "lookup_bypass": lookup_bypass_allowed(),
            }
        )

    def post(self, request):
        landlord_workspace(request)
        serializer = DestinationSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        confirm_identity(request.user, data)
        details = {
            key: data[key] for key in ("kind", "phone", "operator", "bank_id", "account_number")
        }
        if data["kind"] == "bank-account":
            details["bank_name"] = bank_name(data["bank_id"])
        # Ask Lenco outside any lock; the name it returns is what gets saved.
        try:
            lookup = look_up_account(details)
        except AccountNotFound:
            raise
        except ValidationError:
            if not lookup_bypass_allowed() or len(data.get("account_name", "").strip()) < 2:
                raise
            lookup = ""
        with transaction.atomic():
            organization = landlord_workspace(request, lock=True)
            row = approve_destination(
                organization=organization,
                user=request.user,
                account_name=lookup or data["account_name"].strip(),
                lookup_name=lookup,
                reason="Saved by the property manager after password confirmation"
                + ("; name confirmed by Lenco." if lookup else "; Lenco lookup bypassed in test."),
                **details,
            )
            record_event(
                request,
                "payment.destination_saved",
                row,
                organization=organization,
                kind=row.kind,
                account_suffix=(row.account_number or row.phone)[-4:],
                verification="lenco_lookup" if lookup else "test_bypass",
            )
        notify_destination_change(request.user, row)
        return Response(DestinationSerializer(row).data)


class AccountCheckView(PrivateView):
    """Shows Lenco's registered name for receiving details before they are saved."""

    permission_classes = [CanSetReceivingDetails]
    throttle_classes = [PaymentWriteThrottle]

    def post(self, request):
        landlord_workspace(request)
        serializer = AccountDetailsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        details = dict(serializer.validated_data)
        bank = bank_name(details["bank_id"]) if details["kind"] == "bank-account" else ""
        try:
            name = look_up_account(details)
        except AccountNotFound as exc:
            return Response({"found": False, "detail": str(exc.detail[0])})
        except ValidationError:
            if not lookup_bypass_allowed():
                raise
            return Response({"found": None, "detail": "Lenco could not be asked in this test."})
        return Response({"found": True, "account_name": name, "bank_name": bank})


class BankListView(PrivateView):
    permission_classes = [CanSetReceivingDetails]

    def get(self, request):
        landlord_workspace(request)
        return Response({"results": banks()})


class PayoutSummaryView(PrivateView):
    permission_classes = [CanViewPortfolio]

    def get(self, request):
        organization = resolve_workspace(request)
        destination = current_destination(organization)
        totals = balance(organization)
        largest = largest_withdrawal(destination.kind, totals["available"]) if destination else None
        return Response(
            {
                **{key: f"{value:.2f}" for key, value in totals.items()},
                "currency": "ZMW",
                "destination": DestinationSerializer(destination).data if destination else None,
                "withdrawals_enabled": withdrawals_enabled(),
                "minimum": settings.LENCO_WITHDRAWAL_MINIMUM,
                "largest": f"{largest:.2f}" if largest is not None else None,
            }
        )


class WithdrawalPreviewView(PrivateView):
    permission_classes = [CanSetReceivingDetails]

    def post(self, request):
        organization = landlord_workspace(request)
        serializer = WithdrawalPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        destination, amount, fee, available = quote(
            organization, serializer.validated_data["amount"]
        )
        return Response(
            {
                "amount": f"{amount:.2f}",
                "fee": f"{fee:.2f}",
                "total": f"{amount + fee:.2f}",
                "balance_after": f"{available - amount - fee:.2f}",
                "destination": DestinationSerializer(destination).data,
            }
        )


class WithdrawalListView(PrivateView, generics.ListAPIView):
    serializer_class = WithdrawalSerializer

    def get_permissions(self):
        classes = [CanSetReceivingDetails] if self.request.method == "POST" else [CanViewPortfolio]
        return [permission() for permission in classes]

    def get_throttles(self):
        return (
            [PaymentWriteThrottle()] if self.request.method == "POST" else super().get_throttles()
        )

    def get_queryset(self):
        return Withdrawal.objects.filter(
            organization=resolve_workspace(self.request)
        ).select_related("destination")

    def post(self, request):
        organization = landlord_workspace(request)
        serializer = WithdrawalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = request_withdrawal(
            organization=organization, user=request.user, **serializer.validated_data
        )
        record_event(
            request,
            "payment.withdrawal_requested",
            row,
            organization=organization,
            amount=f"{row.amount:.2f}",
            fee_reserved=f"{row.fee_reserved:.2f}",
        )
        return Response(WithdrawalSerializer(row).data, status=201)


class WithdrawalCancelView(PrivateView):
    permission_classes = [CanSetReceivingDetails]
    throttle_classes = [PaymentWriteThrottle]

    def post(self, request, public_id):
        organization = landlord_workspace(request)
        row = get_object_or_404(Withdrawal, organization=organization, public_id=public_id)
        row = cancel_withdrawal(row)
        record_event(request, "payment.withdrawal_cancelled", row, organization=organization)
        return Response(WithdrawalSerializer(row).data)


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
        # A collection's evidence includes its legacy payout; a withdrawal has its own.
        row = Collection.objects.filter(public_id=public_id).first()
        if row is not None:
            scope = Q(collection=row) | Q(payout__collection=row)
        else:
            scope = Q(withdrawal=get_object_or_404(Withdrawal, public_id=public_id))
        exchanges = (
            Exchange.objects.filter(scope).defer("encrypted_payload").order_by("-created_at", "-pk")
        )
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
            row.collection.organization
            if row.collection_id
            else row.withdrawal.organization
            if row.withdrawal_id
            else None,
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
            )
            .select_related("account")
            .first()
            if settings.LENCO_DEBIT_ACCOUNT_ID
            else None
        )
        if snapshot is None:
            return Response(
                {
                    "status": "not_synced",
                    "environment": settings.LENCO_ENVIRONMENT,
                    "currency": "ZMW",
                }
            )
        fields = [
            "status",
            "issue",
            "created_at",
            "available_balance",
            "ledger_balance",
            "expected_balance",
            "difference",
            "held_for_landlords",
            "surplus",
            "credits_total",
            "debits_total",
            "transaction_count",
            "rent_collections_total",
            "rent_settled_total",
            "payouts_total",
            "payout_fees_total",
        ]
        values = {key: getattr(snapshot, key) for key in fields}
        values["checked_at"] = snapshot.account.checked_at
        values["environment"] = snapshot.account.environment
        values["currency"] = snapshot.account.currency
        return Response(
            {
                key: f"{value:.2f}" if isinstance(value, Decimal) else value
                for key, value in values.items()
            }
        )
