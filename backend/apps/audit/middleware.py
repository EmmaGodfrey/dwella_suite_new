import uuid

from django.db import transaction
from rest_framework.permissions import SAFE_METHODS

from apps.common.workspaces import is_workspace_scoped

from .services import record_event


class RequestAuditContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = (request.headers.get("X-Request-ID") or str(uuid.uuid4()))[:120]
        if request.method in SAFE_METHODS or not is_workspace_scoped(request):
            return self.get_response(request)
        # Keep the business write and its audit record in the same transaction.
        with transaction.atomic():
            response = self.get_response(request)
            session = getattr(request, "support_session", None)
            if not session and response.status_code < 400:
                match = request.resolver_match
                important = {
                    "invoice-record-payment": "payment.recorded",
                    "invoice-void": "invoice.voided",
                    "payment-reverse": "payment.reversed",
                    "lease-end": "lease.ended",
                }
                if action := important.get(match.url_name if match else ""):
                    event = record_event(request, action)
                    event.resource_type = {
                        "payment.recorded": "billing.invoice", "invoice.voided": "billing.invoice",
                        "payment.reversed": "billing.payment", "lease.ended": "leases.lease",
                    }[action]
                    event.resource_id = str(match.kwargs.get("public_id", ""))
                    event.save(update_fields=["resource_type", "resource_id"])
            if session and request.method not in {"GET", "HEAD", "OPTIONS"}:
                if response.status_code >= 400:
                    transaction.set_rollback(True)
                elif not getattr(request, "support_event_recorded", False):
                    match = request.resolver_match
                    view = getattr(response, "renderer_context", {}).get("view")
                    action = getattr(view, "action", request.method.lower())
                    resource_type = getattr(getattr(view, "queryset", None), "model", None)
                    if resource_type is None:
                        serializer_class = getattr(view, "serializer_class", None)
                        resource_type = getattr(
                            getattr(serializer_class, "Meta", None), "model", None
                        )
                    event = record_event(
                        request, f"support.{action}", path=request.path, method=request.method
                    )
                    event.resource_type = (
                        resource_type._meta.label_lower if resource_type else type(view).__name__
                    )
                    data = getattr(response, "data", {})
                    event.resource_id = str(
                        match.kwargs.get("public_id")
                        or (data.get("id", "") if isinstance(data, dict) else "")
                        or session.organization.public_id
                    )
                    event.save(update_fields=["resource_type", "resource_id"])
            return response
