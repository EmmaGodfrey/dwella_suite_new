from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from apps.notifications.message_views import (
    ComposeSerializer,
    ConfirmSerializer,
    PreviewResponseSerializer,
    request_data,
)
from apps.notifications.messaging import confirm, preview
from apps.notifications.models import MessageRequest

from .views import ACTION_AUTH, ACTION_EXTENSION, IDEMPOTENCY_PARAMETER, HandyActionView


class PreviewMessageAction(HandyActionView):
    @extend_schema(
        operation_id="assistant_preview_tenant_message",
        summary="Preview a notice to selected tenants; does not send",
        description=(
            "Show exact recipients, content and readiness to the user. "
            "Ask for approval before confirm. This sends a notice, not chat."
        ),
        request=ComposeSerializer,
        responses={201: PreviewResponseSerializer},
        parameters=[IDEMPOTENCY_PARAMETER],
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request):
        data = self.validated(ComposeSerializer)

        def create():
            message = preview(
                organization=self.get_organization(),
                actor=request.user,
                data=data.validated_data,
                source="assistant",
            )
            return request_data(message), message

        return self.execute("message.previewed", create)


class ConfirmMessageAction(HandyActionView):
    @extend_schema(
        operation_id="assistant_confirm_tenant_message",
        summary="Confirm a previously previewed tenant notice after user approval",
        description=(
            "Requires explicit user approval of the exact preview. Pass confirmed=true. "
            "Repeated calls do not send twice. Unconnected channels stay held; "
            "never claim they were delivered."
        ),
        request=ConfirmSerializer,
        responses={201: PreviewResponseSerializer},
        parameters=[IDEMPOTENCY_PARAMETER],
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request, public_id):
        self.validated(ConfirmSerializer)

        def create():
            message = get_object_or_404(
                MessageRequest,
                organization=self.get_organization(),
                actor=request.user,
                public_id=public_id,
            )
            message = confirm(message=message, actor=request.user)
            return request_data(message), message

        return self.execute(f"message.confirmed:{public_id}", create)
