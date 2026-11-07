from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.common.permissions import CanManagePortfolio, IsPlatformSuperuser
from apps.common.workspaces import resolve_workspace
from apps.tenants.models import Tenant

from .messaging import channel_readiness, confirm, preview
from .models import MessageDelivery, MessageRequest


class MessageWriteThrottle(UserRateThrottle):
    scope = "message_write"
    rate = "30/hour"


class ComposeSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=["email", "sms", "whatsapp"])
    tenants = serializers.ListField(
        child=serializers.UUIDField(), max_length=100, required=False, default=list
    )
    all_tenants = serializers.BooleanField(required=False, default=False)
    subject = serializers.CharField(max_length=160)
    body = serializers.CharField(max_length=2000)

    def validate(self, attrs):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError("Unknown message field.")
        if "\n" in attrs["subject"] or "\r" in attrs["subject"]:
            raise serializers.ValidationError({"subject": "Use a single-line subject."})
        if len(set(attrs["tenants"])) != len(attrs["tenants"]):
            raise serializers.ValidationError({"tenants": "Select each tenant once."})
        if attrs["all_tenants"] == bool(attrs["tenants"]):
            raise serializers.ValidationError(
                {"tenants": "Select 1–100 tenants, or choose all active tenants."}
            )
        return attrs


class ConfirmSerializer(serializers.Serializer):
    confirmed = serializers.BooleanField()

    def validate(self, attrs):
        if set(self.initial_data) != {"confirmed"} or not attrs["confirmed"]:
            raise serializers.ValidationError("Explicit confirmation of the preview is required.")
        return attrs


class PreviewResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    channel = serializers.CharField()
    subject = serializers.CharField()
    body = serializers.CharField()
    recipients = serializers.ListField(child=serializers.DictField())
    skipped = serializers.IntegerField(help_text="Active tenants left out for missing contact")
    expires_at = serializers.DateTimeField()
    confirmed_at = serializers.DateTimeField(allow_null=True)
    channels = serializers.DictField(child=serializers.BooleanField())
    delivery_note = serializers.CharField()


def request_data(message):
    return {
        "id": message.public_id,
        "channel": message.channel,
        "subject": message.subject,
        "body": message.body,
        "recipients": message.recipients,
        "skipped": getattr(message, "skipped", 0),
        "expires_at": message.expires_at,
        "confirmed_at": message.confirmed_at,
        "channels": channel_readiness(),
        "delivery_note": "Queued for delivery; recipient consent and channel rules apply."
        if channel_readiness()[message.channel]
        else "Held until delivery is connected. Nothing has been sent.",
    }


class PrivateMessagesMixin:
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


class PreviewView(PrivateMessagesMixin, APIView):
    permission_classes = [CanManagePortfolio]
    throttle_classes = [MessageWriteThrottle]

    @extend_schema(request=ComposeSerializer, responses={201: PreviewResponseSerializer})
    def post(self, request):
        data = ComposeSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        message = preview(
            organization=resolve_workspace(request), actor=request.user, data=data.validated_data
        )
        record_event(
            request,
            "message.previewed",
            message,
            organization=message.organization,
            recipient_count=len(message.recipients),
        )
        return Response(request_data(message), status=201)


class ConfirmView(PreviewView):
    @extend_schema(request=ConfirmSerializer, responses=PreviewResponseSerializer)
    def post(self, request, public_id):
        data = ConfirmSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        message = get_object_or_404(
            MessageRequest,
            public_id=public_id,
            organization=resolve_workspace(request),
            actor=request.user,
        )
        with transaction.atomic():
            message = confirm(message=message, actor=request.user)
            record_event(
                request,
                "message.confirmed",
                message,
                organization=message.organization,
                recipient_count=len(message.recipients),
            )
        return Response(request_data(message))


class RecipientSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id")

    class Meta:
        model = Tenant
        fields = ["id", "full_name", "email", "phone_number"]


class RecipientsView(PrivateMessagesMixin, generics.ListAPIView):
    permission_classes = [CanManagePortfolio]
    serializer_class = RecipientSerializer
    search_fields = ["full_name", "phone_number", "email"]

    def get_queryset(self):
        return (
            Tenant.objects.filter(organization=resolve_workspace(self.request), is_active=True)
            .order_by("full_name")
            .only("public_id", "full_name", "email", "phone_number")
        )


class DeliverySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id")
    tenant_name = serializers.CharField(source="tenant.full_name")
    workspace_name = serializers.CharField(source="organization.name")

    class Meta:
        model = MessageDelivery
        fields = [
            "id",
            "tenant_name",
            "workspace_name",
            "channel",
            "recipient",
            "subject",
            "status",
            "reason",
            "created_at",
            "sent_at",
            "reminder_date",
            "provider",
            "provider_id",
            "delivered_at",
            "read_at",
            "failure_code",
        ]


class MessagesView(PrivateMessagesMixin, generics.ListAPIView):
    permission_classes = [CanManagePortfolio]
    serializer_class = DeliverySerializer
    search_fields = ["subject", "tenant__full_name"]
    filterset_fields = ["channel", "status"]

    def get_queryset(self):
        return (
            MessageDelivery.objects.filter(organization=resolve_workspace(self.request))
            .select_related("tenant", "organization")
            .defer("body")
            .order_by("-created_at", "-pk")
        )


class PlatformMessagesView(MessagesView):
    permission_classes = [IsPlatformSuperuser]

    def get_queryset(self):
        return (
            MessageDelivery.objects.select_related("tenant", "organization")
            .defer("body")
            .order_by("-created_at", "-pk")
        )


class MessageDetailView(PreviewView):
    def get_throttles(self):
        # Reading a message must not use up the sending allowance.
        return [] if self.request.method == "GET" else super().get_throttles()

    def get(self, request, public_id):
        row = get_object_or_404(
            MessageDelivery.objects.select_related("tenant", "organization"),
            public_id=public_id,
            organization=resolve_workspace(request),
        )
        return Response({**DeliverySerializer(row).data, "body": row.body})

    def post(self, request, public_id):
        data = ConfirmSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        row = get_object_or_404(
            MessageDelivery, public_id=public_id, organization=resolve_workspace(request)
        )
        MessageDelivery.objects.filter(pk=row.pk, status__in=["held", "queued"]).update(
            status="cancelled", reason="cancelled_by_manager"
        )
        record_event(request, "message.cancelled", row, organization=row.organization)
        return Response(
            {"cancelled": MessageDelivery.objects.filter(pk=row.pk, status="cancelled").exists()}
        )
