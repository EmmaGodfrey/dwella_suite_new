from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.billing.models import InvoiceLine
from apps.billing.services import create_invoice
from apps.common.references import next_reference

from .models import MaintenanceRequest, MaintenanceUpdate

Status = MaintenanceRequest.Status
# How long a tenant has to pay for a repair they were charged for.
REPAIR_CHARGE_TERMS = timedelta(days=14)


def log_status(request, body, author=None):
    return MaintenanceUpdate.objects.create(
        request=request, author=author, kind=MaintenanceUpdate.Kind.STATUS, body=body
    )


def locked(request):
    return MaintenanceRequest.objects.select_for_update().get(pk=request.pk)


def require_status(request, allowed, message):
    if request.status not in allowed:
        raise ValidationError({"status": [message]})


@transaction.atomic
def create_request(*, organization, reported_by=None, **fields):
    request = MaintenanceRequest.objects.create(
        organization=organization,
        reference=next_reference(organization, MaintenanceRequest, "MR"),
        reported_by=reported_by,
        **fields,
    )
    log_status(request, "Request reported.", reported_by)
    return request


@transaction.atomic
def assign_request(
    request, *, vendor, scheduled_for=None, estimated_cost=None, charge_to_tenant=None, author=None
):
    request = locked(request)
    require_status(
        request,
        (Status.NEW, Status.SCHEDULED, Status.IN_PROGRESS),
        "Only an open request can be assigned.",
    )
    request.vendor = vendor
    request.scheduled_for = scheduled_for
    request.estimated_cost = estimated_cost
    if charge_to_tenant is not None:
        request.charge_to_tenant = charge_to_tenant
    if request.charge_to_tenant and request.tenant_id is None:
        raise ValidationError(
            {"charge_to_tenant": ["Link a tenant to the request before charging them."]}
        )
    if request.status == Status.NEW:
        request.status = Status.SCHEDULED
    request.save()
    when = f" for {timezone.localtime(scheduled_for):%a %d %b, %H:%M}" if scheduled_for else ""
    log_status(request, f"Assigned to {vendor.name}{when}.", author)
    return request


@transaction.atomic
def start_request(request, author=None):
    request = locked(request)
    require_status(
        request, (Status.NEW, Status.SCHEDULED), "Only a new or scheduled request can be started."
    )
    request.status = Status.IN_PROGRESS
    request.started_at = timezone.now()
    request.save(update_fields=["status", "started_at", "updated_at"])
    log_status(request, "Work started.", author)
    return request


@transaction.atomic
def complete_request(request, *, actual_cost=None, author=None):
    """Close the job; bill the tenant for it if the landlord chose to."""
    request = locked(request)
    require_status(request, MaintenanceRequest.OPEN_STATUSES, "This request is already closed.")
    if actual_cost is not None:
        request.actual_cost = actual_cost
    request.status = Status.COMPLETED
    request.completed_at = timezone.now()
    cost = request.actual_cost if request.actual_cost is not None else request.estimated_cost
    if request.charge_to_tenant and request.tenant_id and cost:
        today = timezone.localdate()
        request.invoice = create_invoice(
            organization=request.organization,
            tenant=request.tenant,
            unit=request.unit,
            issue_date=today,
            due_date=today + REPAIR_CHARGE_TERMS,
            lines=[
                {
                    "kind": InvoiceLine.Kind.OTHER,
                    "description": f"Repair · {request.reference} {request.title}"[:200],
                    "amount": cost,
                }
            ],
        )
    request.save()
    note = "Marked as done."
    if request.invoice_id:
        note = f"Marked as done. Tenant charged on {request.invoice.reference}."
    log_status(request, note, author)
    return request


@transaction.atomic
def cancel_request(request, *, reason="", author=None):
    request = locked(request)
    require_status(request, MaintenanceRequest.OPEN_STATUSES, "This request is already closed.")
    request.status = Status.CANCELLED
    request.cancelled_at = timezone.now()
    request.save(update_fields=["status", "cancelled_at", "updated_at"])
    log_status(request, f"Cancelled. {reason}".strip() if reason else "Cancelled.", author)
    return request
