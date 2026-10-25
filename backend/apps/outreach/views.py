from collections.abc import Mapping
from hashlib import sha256

from django.conf import settings
from django.core import signing
from django.db import IntegrityError, transaction
from django.db.models import Count, Exists, OuterRef
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditEvent
from apps.audit.services import record_event
from apps.common.permissions import IsPlatformAdmin

from .csv_import import SALT, preview_import
from .early_access import give_early_access
from .models import (
    LIVE_ENROLLMENTS,
    Contact,
    Enrollment,
    ImportReceipt,
    OutreachMessage,
    OutreachSettings,
    Sequence,
    Suppression,
    Template,
)
from .rendering import FIELDS, render_template
from .serializers import (
    ContactSerializer,
    EnrollmentSerializer,
    MessageSerializer,
    SequenceSerializer,
    SettingsSerializer,
    TemplateSerializer,
)
from .services import (
    approve_enrollment,
    change_contact_status,
    ensure_contact_allowed,
    review_snapshot,
)


class AuditedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsPlatformAdmin]
    lookup_field = "public_id"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method in ("POST", "PATCH") and not isinstance(request.data, Mapping):
            raise serializers.ValidationError("Expected a JSON object.")

    def get_throttles(self):
        self.throttle_scope = (
            "platform_write" if self.request.method not in ("GET", "HEAD") else None
        )
        return super().get_throttles()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                return super().create(request, *args, **kwargs)
        except IntegrityError as error:
            raise serializers.ValidationError("This record already exists or conflicts.") from error

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                return super().update(request, *args, **kwargs)
        except IntegrityError as error:
            raise serializers.ValidationError("This record already exists or conflicts.") from error

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if isinstance(obj, Template | Sequence):
            raise serializers.ValidationError("Archive this template or sequence instead.")
        record_event(request, f"outreach.{obj._meta.model_name}.deleted", obj)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        obj = serializer.save()
        record_event(self.request, f"outreach.{obj._meta.model_name}.created", obj)

    def perform_update(self, serializer):
        extra = (
            {"version": serializer.instance.version + 1}
            if isinstance(
                serializer.instance,
                Template,
            )
            else {}
        )
        obj = serializer.save(**extra)
        record_event(self.request, f"outreach.{obj._meta.model_name}.updated", obj)


class ContactViewSet(AuditedViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    search_fields = ["name", "email", "organization", "phone", "handle", "town"]
    filterset_fields = ["segment", "status", "platform"]

    def get_queryset(self):
        query = super().get_queryset()
        if self.action in ("list", "retrieve"):
            query = query.annotate(
                has_suppression=Exists(Suppression.objects.filter(email__iexact=OuterRef("email")))
            )
        return query

    @action(detail=True, methods=["post"], url_path="early-access")
    def early_access(self, request, public_id=None):
        return Response(self.get_serializer(give_early_access(self.get_object(), request)).data)

    def perform_create(self, serializer):
        obj = serializer.save(owner=self.request.user)
        if obj.email and Suppression.objects.filter(email__iexact=obj.email).exists():
            obj.status = "do_not_contact"
            obj.save(update_fields=["status"])
        record_event(self.request, "outreach.contact.created", obj)

    def perform_update(self, serializer):
        obj = Contact.objects.select_for_update().get(pk=serializer.instance.pk)
        if obj.enrollments.filter(status__in=LIVE_ENROLLMENTS, approved_at__isnull=False).exists():
            raise serializers.ValidationError(
                "Stop the approved sequence before editing this contact; then review it again.",
            )
        super().perform_update(serializer)

    @action(detail=True, methods=["post"], url_path="status")
    @transaction.atomic
    def set_status(self, request, public_id=None):
        value = request.data.get("status")
        if value not in ("replied", "interested", "partner", "not_interested", "do_not_contact"):
            raise serializers.ValidationError({"status": "Choose a supported contact action."})
        contact = change_contact_status(self.get_object(), value)
        record_event(request, "outreach.contact.status_changed", contact, status=value)
        return Response(self.get_serializer(contact).data)

    @action(detail=True, methods=["get"])
    def activity(self, request, public_id=None):
        contact = self.get_object()
        events = AuditEvent.objects.filter(
            resource_type="outreach.contact", resource_id=str(contact.public_id)
        ).order_by("-created_at")
        page = self.paginate_queryset(events)
        return self.get_paginated_response(
            [
                {
                    "id": str(e.public_id),
                    "action": e.action,
                    "created_at": e.created_at,
                    "status": e.metadata.get("status", ""),
                }
                for e in page
            ]
        )

    @action(detail=False, methods=["post"], url_path="import-preview")
    def import_preview(self, request):
        return Response(preview_import(request.data))

    @action(detail=False, methods=["post"], url_path="import-confirm")
    @transaction.atomic
    def import_confirm(self, request):
        token = serializers.CharField(max_length=2_000_000).run_validation(
            request.data.get("preview_token"),
        )
        try:
            rows = signing.loads(token, salt=SALT, max_age=600)
        except signing.BadSignature as error:
            raise serializers.ValidationError(
                "Preview expired or changed. Preview the CSV again."
            ) from error
        # One lock serializes imports; unique indexes also protect direct creates.
        OutreachSettings.objects.get_or_create(pk=1)
        OutreachSettings.objects.select_for_update().get(pk=1)
        _, first_import = ImportReceipt.objects.get_or_create(
            digest=sha256(token.encode()).hexdigest(),
        )
        if not first_import:
            raise serializers.ValidationError("This preview was already imported. Preview again.")
        created = 0
        for row in rows:
            serializer = self.get_serializer(data=row)
            if not serializer.is_valid():
                continue
            email = serializer.validated_data.get("email")
            if email and Suppression.objects.filter(email__iexact=email).exists():
                continue
            try:
                with transaction.atomic():
                    self.perform_create(serializer)
                    created += 1
            except IntegrityError:
                continue
        return Response({"created": created, "skipped": len(rows) - created})


class TemplateViewSet(AuditedViewSet):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer
    search_fields = ["name", "subject"]
    filterset_fields = ["active", "segment"]

    @action(detail=True, methods=["post"])
    def preview(self, request, public_id=None):
        contact = serializers.SlugRelatedField(
            slug_field="public_id",
            queryset=Contact.objects.all(),
        ).run_validation(request.data.get("contact"))
        line = serializers.CharField(max_length=1000, allow_blank=True).run_validation(
            request.data.get("personal_line", ""),
        )
        config, _ = OutreachSettings.objects.get_or_create(pk=1)
        return Response(render_template(self.get_object(), contact, config, line))

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def whatsapp(self, request, public_id=None):
        contact = serializers.SlugRelatedField(
            slug_field="public_id",
            queryset=Contact.objects.all(),
        ).run_validation(request.data.get("contact"))
        if contact.status in ("do_not_contact", "bounced", "not_interested") or (
            contact.email and Suppression.objects.filter(email__iexact=contact.email).exists()
        ):
            raise serializers.ValidationError("This contact is suppressed.")
        if not contact.whatsapp:
            raise serializers.ValidationError("Add the contact's WhatsApp number first.")
        config, _ = OutreachSettings.objects.get_or_create(pk=1)
        message = render_template(self.get_object(), contact, config, whatsapp=True)
        record_event(request, "outreach.contact.whatsapp_opened", contact)
        return Response({"body": message["body"], "number": contact.whatsapp})


class SequenceViewSet(AuditedViewSet):
    queryset = Sequence.objects.prefetch_related("steps__template")
    serializer_class = SequenceSerializer
    search_fields = ["name"]
    filterset_fields = ["active"]


class EnrollmentViewSet(AuditedViewSet):
    queryset = Enrollment.objects.select_related("contact", "sequence")
    serializer_class = EnrollmentSerializer
    filterset_fields = ["status", "contact__public_id"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def perform_create(self, serializer):
        contact = Contact.objects.select_for_update().get(
            pk=serializer.validated_data["contact"].pk
        )
        ensure_contact_allowed(contact)
        if not serializer.validated_data["sequence"].active:
            raise serializers.ValidationError("Choose an active sequence.")
        super().perform_create(serializer)
        contact.status = "queued"
        contact.save(update_fields=["status", "updated_at"])

    def perform_update(self, serializer):
        obj = self.get_object()
        if obj.status != "pending_review" or set(serializer.validated_data) - {"personal_line"}:
            raise serializers.ValidationError(
                "Only the opening line of a pending review can change."
            )
        super().perform_update(serializer)

    @action(detail=True, methods=["get"])
    def preview(self, request, public_id=None):
        obj = self.get_object()
        ensure_contact_allowed(obj.contact)
        return Response(review_snapshot(obj))

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def approve(self, request, public_id=None):
        obj = approve_enrollment(self.get_object(), request.user, request.data.get("preview_token"))
        record_event(request, "outreach.enrollment.approved", obj)
        return Response(self.get_serializer(obj).data)

    @action(detail=False, methods=["post"], url_path="approve-many")
    @transaction.atomic
    def approve_many(self, request):
        ids = serializers.ListField(
            child=serializers.UUIDField(), min_length=1, max_length=100
        ).run_validation(request.data.get("ids"))
        for public_id in sorted(set(ids)):
            obj = self.get_queryset().filter(public_id=public_id).first()
            if not obj:
                raise serializers.ValidationError("A selected review no longer exists.")
            tokens = request.data.get("tokens", {})
            if not isinstance(tokens, dict):
                raise serializers.ValidationError("Preview each selected email first.")
            obj = approve_enrollment(obj, request.user, tokens.get(str(public_id)))
            record_event(request, "outreach.enrollment.approved", obj)
        return Response({"approved": len(set(ids))})

    @action(detail=True, methods=["post"], url_path="state")
    @transaction.atomic
    def state(self, request, public_id=None):
        obj = Enrollment.objects.select_for_update().get(pk=self.get_object().pk)
        command = request.data.get("action")
        if command == "stop" and obj.status in LIVE_ENROLLMENTS:
            obj.status, obj.next_send_at = "cancelled", None
        elif command == "pause" and obj.status in ("scheduled", "active"):
            obj.status = "paused"
        elif command == "resume" and obj.status == "paused" and obj.approved_at:
            ensure_contact_allowed(obj.contact)
            obj.status, obj.next_send_at = "scheduled", timezone.now()
        elif command == "send_next" and obj.status in ("scheduled", "active") and obj.approved_at:
            ensure_contact_allowed(obj.contact)
            obj.next_send_at = timezone.now()
        else:
            raise serializers.ValidationError("This action is not available for this enrollment.")
        obj.save()
        record_event(request, f"outreach.enrollment.{command}", obj)
        return Response(self.get_serializer(obj).data)


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OutreachMessage.objects.select_related("enrollment__contact")
    serializer_class = MessageSerializer
    permission_classes = [IsPlatformAdmin]
    lookup_field = "public_id"
    filterset_fields = ["status", "enrollment__contact__public_id"]


class OutreachSettingsView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get_throttles(self):
        self.throttle_scope = "platform_write" if self.request.method == "PATCH" else None
        return super().get_throttles()

    def get(self, request):
        config, _ = OutreachSettings.objects.get_or_create(pk=1)
        return Response(
            {
                **SettingsSerializer(config).data,
                "enabled": getattr(settings, "OUTREACH_ENABLED", False),
                "from_address": getattr(settings, "OUTREACH_FROM_ADDRESS", ""),
                "merge_fields": FIELDS,
            }
        )

    @transaction.atomic
    def patch(self, request):
        OutreachSettings.objects.get_or_create(pk=1)
        config = OutreachSettings.objects.select_for_update().get(pk=1)
        serializer = SettingsSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_event(request, "outreach.settings.updated", config)
        return self.get(request)


class SummaryView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        today = timezone.localdate()
        config, _ = OutreachSettings.objects.get_or_create(pk=1)
        sent = OutreachMessage.objects.filter(status="sent", sent_at__date=today).count()
        return Response(
            {
                "contacts": Contact.objects.count(),
                "awaiting_review": Enrollment.objects.filter(status="pending_review").count(),
                "sent_today": sent,
                "remaining_today": max(0, config.daily_cap - sent),
                "daily_cap": config.daily_cap,
                "paused": config.paused,
                "replies": Contact.objects.filter(replied_at__isnull=False).count(),
                "statuses": list(
                    OutreachMessage.objects.order_by()
                    .values("status")
                    .annotate(
                        count=Count("pk"),
                    )
                ),
            }
        )
