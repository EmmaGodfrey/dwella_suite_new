"""Bounded tenant notices derived from records the portal already permits."""

from datetime import timedelta

from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.billing.models import Invoice, Payment
from apps.documents.models import DocumentSignature, DocumentVersion
from apps.leases.models import Lease
from apps.maintenance.models import MaintenanceRequest, MaintenanceUpdate

SOURCE_LIMIT = 100
FEED_LIMIT = 200


def tenant_alerts(portal, user):
    now = timezone.now()
    today = timezone.localdate(now)
    since = now - timedelta(days=30)
    alerts = []

    def add(key, kind, title, body, path, date):
        alerts.append(
            {
                "id": key,
                "kind": kind,
                "title": title,
                "body": body,
                "path": path,
                "date": date.isoformat(),
            }
        )

    for invoice in (
        portal.scope(
            Invoice.objects.filter(
                is_active=True,
                status__in=Invoice.UNPAID_STATUSES,
            )
        )
        .only("public_id", "reference", "due_date", "total", "amount_paid")
        .order_by("due_date", "pk")[:SOURCE_LIMIT]
    ):
        overdue = invoice.due_date < today
        add(
            f"invoice:{invoice.public_id}:{'overdue' if overdue else 'due'}",
            "arrears" if overdue else "payment",
            f"{invoice.reference} is overdue" if overdue else "Invoice available",
            (
                f"{portal.organization.currency} {invoice.balance:.2f} outstanding "
                f"· Due {invoice.due_date}"
            ),
            f"/billing?invoice={invoice.public_id}",
            invoice.due_date,
        )

    for payment in (
        portal.scope(
            Payment.objects.filter(is_active=True).filter(
                Q(created_at__gte=since) | Q(reversed_at__gte=since)
            )
        )
        .only("public_id", "receipt_number", "amount", "created_at", "reversed_at")
        .order_by("-created_at", "-pk")[:SOURCE_LIMIT]
    ):
        reversed_payment = bool(payment.reversed_at)
        add(
            f"payment:{payment.public_id}:{'reversed' if reversed_payment else 'confirmed'}",
            "payment",
            "Payment corrected" if reversed_payment else "Payment received",
            f"{payment.receipt_number} · {portal.organization.currency} {payment.amount:.2f}",
            f"/billing/receipts/{payment.public_id}",
            payment.reversed_at or payment.created_at,
        )

    for lease in (
        portal.scope(
            Lease.objects.filter(
                is_active=True,
                status=Lease.Status.ACTIVE,
                end_date__lte=today + timedelta(days=30),
            )
        )
        .only("public_id", "reference", "end_date")
        .order_by("end_date", "pk")[:SOURCE_LIMIT]
    ):
        add(
            f"lease:{lease.public_id}:{lease.end_date}",
            "lease",
            "Lease has expired" if lease.end_date < today else "Lease ends soon",
            f"{lease.reference} · Ends {lease.end_date}",
            f"/leases/{lease.public_id}",
            lease.end_date,
        )

    documents = (
        DocumentVersion.objects.filter(
            organization=portal.organization,
            is_active=True,
            kind=DocumentVersion.Kind.LEASE,
            lease__tenant_id__in=portal.tenant_ids,
            lease__is_active=True,
            lease__status__in=[
                Lease.Status.PENDING_SIGNATURE,
                Lease.Status.ACTIVE,
                Lease.Status.ENDED,
            ],
        )
        .annotate(
            tenant_signed=Exists(
                DocumentSignature.objects.filter(
                    document_id=OuterRef("pk"),
                    role="tenant",
                )
            )
        )
        .filter(
            Q(status=DocumentVersion.Status.SIGNING, tenant_signed=False)
            | Q(status=DocumentVersion.Status.SIGNED, updated_at__gte=since)
        )
        .values("public_id", "status", "updated_at", "lease__public_id", "lease__reference")
        .order_by("-updated_at", "-pk")[:SOURCE_LIMIT]
    )
    for document in documents:
        signed = document["status"] == DocumentVersion.Status.SIGNED
        add(
            f"document:{document['public_id']}:{document['status']}",
            "lease",
            "Lease signing completed" if signed else "Lease awaiting your signature",
            f"{document['lease__reference']} · "
            + (
                "Your signed agreement is available."
                if signed
                else "Open your lease to review signing instructions."
            ),
            f"/leases/{document['lease__public_id']}",
            document["updated_at"],
        )

    repairs = (
        portal.scope(MaintenanceRequest.objects.filter(is_active=True))
        .filter(
            Q(status__in=MaintenanceRequest.OPEN_STATUSES)
            | Q(completed_at__gte=since)
            | Q(cancelled_at__gte=since)
        )
        .only(
            "public_id",
            "reference",
            "title",
            "status",
            "scheduled_for",
            "created_at",
            "started_at",
            "completed_at",
            "cancelled_at",
        )
        .order_by("-created_at", "-pk")[:SOURCE_LIMIT]
    )
    for repair in repairs:
        schedule = repair.scheduled_for.isoformat() if repair.scheduled_for else "none"
        add(
            f"repair:{repair.public_id}:{repair.status}:{schedule}",
            "maintenance",
            f"Repair {repair.get_status_display().lower()}",
            f"{repair.reference} · {repair.title}",
            f"/maintenance/{repair.public_id}",
            repair.completed_at or repair.cancelled_at or repair.started_at or repair.created_at,
        )

    updates = (
        MaintenanceUpdate.objects.filter(
            request__organization=portal.organization,
            request__tenant_id__in=portal.tenant_ids,
            request__is_active=True,
            is_internal=False,
            kind=MaintenanceUpdate.Kind.COMMENT,
            created_at__gte=since,
        )
        .exclude(author=user)
        .values(
            "pk",
            "request__public_id",
            "request__reference",
            "request__title",
            "created_at",
        )
        .order_by("-created_at", "-pk")[:SOURCE_LIMIT]
    )
    for update in updates:
        add(
            f"repair_update:{update['request__public_id']}:{update['pk']}",
            "maintenance",
            "New repair update",
            f"{update['request__reference']} · {update['request__title']}",
            f"/maintenance/{update['request__public_id']}",
            update["created_at"],
        )

    # Keep mandatory overdue notices in the bounded feed, then the newest events.
    overdue = sorted((a for a in alerts if a["kind"] == "arrears"), key=lambda a: a["date"])
    recent = sorted(
        (a for a in alerts if a["kind"] != "arrears"),
        key=lambda a: (a["date"], a["id"]),
        reverse=True,
    )
    return (overdue + recent)[:FEED_LIMIT]
