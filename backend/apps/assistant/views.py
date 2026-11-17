import hashlib
import json
import re

from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError, transaction
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import HandyActionExecution
from apps.audit.services import record_event
from apps.billing.models import Invoice
from apps.billing.serializers import PaymentSerializer
from apps.billing.services import record_payment
from apps.common.property_scope import (
    cover_event_details,
    property_ids_of,
    property_scope,
    require_in_scope,
    require_property_admin,
    scoped_object,
)
from apps.maintenance.models import MaintenanceRequest, MaintenanceUpdate

from .authentication import HandyAgentAuthentication
from .serializers import (
    AssistantDraftLeaseSerializer,
    AssistantInvoiceSerializer,
    AssistantMaintenanceCommentSerializer,
    AssistantMaintenanceRequestSerializer,
    AssistantPropertySerializer,
    AssistantRecordPaymentSerializer,
    AssistantTenantSerializer,
    AssistantUnitSerializer,
    AssistantVendorSerializer,
)

ACTION_EXTENSION = {"x-agent": {"enabled": True}}
ACTION_AUTH = [{"HandyAgentBearer": []}]
IDEMPOTENCY_PARAMETER = OpenApiParameter(
    name="Idempotency-Key",
    type=str,
    location=OpenApiParameter.HEADER,
    required=False,
    description="Optional stable key for safely retrying this approved action.",
)


class ActionConflict(APIException):
    status_code = 409
    default_detail = "This assistant action conflicts with an earlier request."
    default_code = "assistant_action_conflict"


class HandyActionView(APIView):
    authentication_classes = [HandyAgentAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_scope = "handy_agent_action"

    def get_organization(self):
        return self.request.auth.organization

    def serializer_context(self):
        return {"request": self.request, "view": self}

    def validated(self, serializer_class):
        serializer = serializer_class(data=self.request.data, context=self.serializer_context())
        serializer.is_valid(raise_exception=True)
        return serializer

    def execute(self, operation, callback):
        encoded = json.dumps(
            {
                "method": self.request.method,
                "path": self.request.path_info,
                "data": self.request.data,
            },
            cls=DjangoJSONEncoder,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        payload_hash = hashlib.sha256(encoded).hexdigest()
        supplied_key = self.request.headers.get("Idempotency-Key", "").strip()
        if supplied_key and not re.fullmatch(r"[A-Za-z0-9._:-]{8,160}", supplied_key):
            raise ActionConflict(
                "Idempotency-Key must be 8 to 160 letters, numbers, dots, "
                "underscores, colons, or hyphens."
            )
        idempotency_key = supplied_key or f"{self.request.auth.jti}:{payload_hash}"
        organization = self.get_organization()

        with transaction.atomic():
            lookup = {
                "organization": organization,
                "actor": self.request.user,
                "operation": operation,
                "idempotency_key": idempotency_key,
            }
            previous = (
                HandyActionExecution.objects.select_for_update()
                .filter(**lookup)
                .first()
            )
            execution = None
            if previous is None:
                try:
                    # The savepoint keeps the outer transaction usable when two
                    # identical approved calls arrive at the same time.
                    with transaction.atomic():
                        execution = HandyActionExecution.objects.create(
                            **lookup,
                            payload_hash=payload_hash,
                        )
                except IntegrityError:
                    previous = HandyActionExecution.objects.select_for_update().get(**lookup)
            if previous:
                if previous.payload_hash != payload_hash:
                    raise ActionConflict(
                        "That Idempotency-Key was already used with different data."
                    )
                if previous.completed_at is None:
                    raise ActionConflict("That assistant action is still being processed.")
                if operation == "property.created":
                    require_property_admin(self.request)
                saved_scope_ids = previous.response_data.get("_handy_scope_property_ids")
                current_scope = property_scope(self.request)
                if not current_scope.everything:
                    if saved_scope_ids is None:
                        raise PermissionDenied(
                            "The earlier action's property scope cannot be verified."
                        )
                    if not set(saved_scope_ids).issubset(current_scope.ids):
                        raise NotFound("The earlier action is outside your current property scope.")
                public_response = {
                    key: value for key, value in previous.response_data.items()
                    if key != "_handy_scope_property_ids"
                }
                return Response(public_response, status=previous.response_status)

            result = callback()
            response_data, resource = result[:2]
            scope_property_ids = set(result[2]) if len(result) > 2 else property_ids_of(resource)
            if not property_scope(self.request).everything and not scope_property_ids.issubset(
                property_scope(self.request).ids
            ):
                raise PermissionDenied("This action is outside your current property scope.")
            if len(result) <= 2:
                require_in_scope(self.request, resource)
            else:
                from apps.common.property_scope import touch

                touch(self.request, *scope_property_ids)
            response_data = json.loads(json.dumps(response_data, cls=DjangoJSONEncoder))
            execution.response_data = response_data
            execution.response_data["_handy_scope_property_ids"] = sorted(scope_property_ids)
            execution.response_status = 201
            execution.completed_at = timezone.now()
            execution.save(
                update_fields=["response_data", "response_status", "completed_at"]
            )
            cover_details = cover_event_details(self.request) or {}
            record_event(
                self.request,
                f"assistant.{operation}",
                resource,
                organization=organization,
                handy_jti=self.request.auth.jti,
                idempotency_key=idempotency_key,
                **cover_details,
            )
            return Response(response_data, status=201)

    def create_resource(self, operation, serializer_class, **save_kwargs):
        serializer = self.validated(serializer_class)

        def create():
            instance = serializer.save(organization=self.get_organization(), **save_kwargs)
            output = serializer_class(instance, context=self.serializer_context()).data
            return output, instance

        return self.execute(operation, create)


class CreatePropertyView(HandyActionView):
    @extend_schema(
        operation_id="assistant_create_property",
        summary="Create one property",
        description="Creates a workspace-wide property; property-admin access is required.",
        request=AssistantPropertySerializer,
        responses={201: AssistantPropertySerializer},
        parameters=[IDEMPOTENCY_PARAMETER],
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request):
        # Creating a workspace-wide property is reserved for its property admin.
        require_property_admin(request)
        return self.create_resource("property.created", AssistantPropertySerializer)


class CreateUnitView(HandyActionView):
    @extend_schema(
        operation_id="assistant_create_unit",
        summary="Create one unit in a property",
        request=AssistantUnitSerializer,
        responses={201: AssistantUnitSerializer},
        parameters=[IDEMPOTENCY_PARAMETER],
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request):
        return self.create_resource("unit.created", AssistantUnitSerializer)


class CreateTenantView(HandyActionView):
    @extend_schema(
        operation_id="assistant_create_tenant",
        summary="Create one tenant without activating a lease",
        request=AssistantTenantSerializer,
        responses={201: AssistantTenantSerializer},
        parameters=[IDEMPOTENCY_PARAMETER],
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request):
        return self.create_resource(
            "tenant.created", AssistantTenantSerializer, created_by=request.user
        )


class CreateDraftLeaseView(HandyActionView):
    @extend_schema(
        operation_id="assistant_create_draft_lease",
        summary="Create a draft lease",
        description="Creates a draft only. This action cannot activate a lease.",
        request=AssistantDraftLeaseSerializer,
        responses={201: AssistantDraftLeaseSerializer},
        parameters=[IDEMPOTENCY_PARAMETER],
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request):
        return self.create_resource("draft_lease.created", AssistantDraftLeaseSerializer)


class CreateInvoiceView(HandyActionView):
    @extend_schema(
        operation_id="assistant_create_invoice",
        summary="Create an invoice for a tenant",
        description="Creates an invoice and changes the tenant balance after user approval.",
        request=AssistantInvoiceSerializer,
        responses={201: AssistantInvoiceSerializer},
        parameters=[IDEMPOTENCY_PARAMETER],
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request):
        return self.create_resource("invoice.created", AssistantInvoiceSerializer)


class RecordInvoicePaymentView(HandyActionView):
    @extend_schema(
        operation_id="assistant_record_invoice_payment",
        summary="Record a manual payment against an invoice",
        description="Records a receipt and changes the invoice balance after user approval.",
        request=AssistantRecordPaymentSerializer,
        responses={201: PaymentSerializer},
        parameters=[IDEMPOTENCY_PARAMETER],
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request, public_id):
        serializer = self.validated(AssistantRecordPaymentSerializer)

        def create():
            invoice = scoped_object(
                self.request,
                Invoice.objects.for_organization(self.get_organization()),
                public_id=public_id,
            )
            data = serializer.validated_data
            payment = record_payment(
                invoice=invoice,
                amount=data["amount"],
                method=data["method"],
                paid_on=data.get("paid_on") or timezone.localdate(),
                reference=data["reference"].strip(),
                notes=data["notes"].strip(),
                recorded_by=request.user,
            )
            output = PaymentSerializer(payment, context=self.serializer_context()).data
            return output, payment

        return self.execute("payment.recorded", create)


class CreateVendorView(HandyActionView):
    @extend_schema(
        operation_id="assistant_create_vendor",
        summary="Create a maintenance vendor",
        request=AssistantVendorSerializer,
        responses={201: AssistantVendorSerializer},
        parameters=[IDEMPOTENCY_PARAMETER],
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request):
        return self.create_resource("vendor.created", AssistantVendorSerializer)


class CreateMaintenanceRequestView(HandyActionView):
    @extend_schema(
        operation_id="assistant_create_maintenance_request",
        summary="Create a maintenance request",
        request=AssistantMaintenanceRequestSerializer,
        responses={201: AssistantMaintenanceRequestSerializer},
        parameters=[IDEMPOTENCY_PARAMETER],
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request):
        return self.create_resource(
            "maintenance_request.created",
            AssistantMaintenanceRequestSerializer,
        )


class CreateMaintenanceCommentView(HandyActionView):
    @extend_schema(
        operation_id="assistant_create_maintenance_comment",
        summary="Add a comment to a maintenance request",
        request=AssistantMaintenanceCommentSerializer,
        responses={201: AssistantMaintenanceCommentSerializer},
        parameters=[IDEMPOTENCY_PARAMETER],
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request, public_id):
        serializer = self.validated(AssistantMaintenanceCommentSerializer)

        def create():
            maintenance_request = scoped_object(
                self.request,
                MaintenanceRequest.objects.for_organization(self.get_organization()),
                public_id=public_id,
            )
            comment = serializer.save(
                request=maintenance_request,
                author=request.user,
                kind=MaintenanceUpdate.Kind.COMMENT,
            )
            output = AssistantMaintenanceCommentSerializer(
                comment, context=self.serializer_context()
            ).data
            return output, maintenance_request

        return self.execute("maintenance_comment.created", create)
