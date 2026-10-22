from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Invoice, Payment
from apps.common.permissions import CanViewPortfolio
from apps.common.workspaces import resolve_workspace
from apps.leases.models import Lease
from apps.maintenance.models import MaintenanceRequest

from .models import NotificationRead


def live_alerts(org):
    today = timezone.localdate()
    alerts = []
    for invoice in (
        Invoice.objects.for_organization(org)
        .filter(status__in=Invoice.UNPAID_STATUSES, due_date__lt=today)
        .select_related("tenant")
        .order_by("due_date", "pk")[:100]
    ):
        alerts.append(
            {
                "id": f"invoice:{invoice.public_id}",
                "kind": "arrears",
                "title": f"{invoice.reference} is overdue",
                "body": (
                    f"{invoice.tenant.full_name} · "
                    f"{org.currency} {invoice.balance:.2f} outstanding"
                ),
                "path": f"/billing/invoices/{invoice.public_id}",
                "date": invoice.due_date.isoformat(),
            }
        )
    for lease in (
        Lease.objects.for_organization(org)
        .filter(status=Lease.Status.ACTIVE, end_date__lte=today + timedelta(days=30))
        .select_related("tenant", "unit")
        .order_by("end_date", "pk")[:100]
    ):
        alerts.append(
            {
                "id": f"lease:{lease.public_id}:{lease.end_date}",
                "kind": "lease",
                "title": (
                    f"{lease.reference} "
                    f"{'has expired' if lease.end_date < today else 'ends soon'}"
                ),
                "body": f"{lease.tenant.full_name} · {lease.unit.name}",
                "path": f"/leases/{lease.public_id}",
                "date": lease.end_date.isoformat(),
            }
        )
    for repair in (
        MaintenanceRequest.objects.for_organization(org)
        .filter(status__in=MaintenanceRequest.OPEN_STATUSES)
        .order_by("created_at", "pk")[:100]
    ):
        alerts.append(
            {
                "id": f"repair:{repair.public_id}",
                "kind": "maintenance",
                "title": f"{repair.reference} · {repair.get_priority_display()}",
                "body": repair.title,
                "path": f"/maintenance/{repair.public_id}",
                "date": repair.created_at.date().isoformat(),
            }
        )
    for payment in (
        Payment.objects.for_organization(org)
        .filter(reversed_at__isnull=True, created_at__gte=timezone.now() - timedelta(days=7))
        .select_related("tenant")
        .order_by("-created_at", "pk")[:100]
    ):
        alerts.append(
            {
                "id": f"payment:{payment.public_id}",
                "kind": "payment",
                "title": f"{payment.receipt_number} · Payment received",
                "body": f"{payment.tenant.full_name} · {org.currency} {payment.amount:.2f}",
                "path": f"/billing/receipts/{payment.public_id}",
                "date": timezone.localtime(payment.created_at).date().isoformat(),
            }
        )
    return sorted(alerts, key=lambda alert: (alert["date"], alert["id"]))


class ReadSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.CharField(max_length=100), min_length=1, max_length=400
    )


class NotificationsView(APIView):
    permission_classes = [IsAuthenticated, CanViewPortfolio]

    def organization(self):
        return resolve_workspace(self.request)

    def get(self, request):
        org = self.organization()
        alerts = live_alerts(org) if org else []
        read = set(
            NotificationRead.objects.filter(organization=org, user=request.user).values_list(
                "key", flat=True
            )
        )
        for alert in alerts:
            alert["read"] = alert["id"] in read
        return Response(
            {
                "items": alerts,
                "unread_count": sum(not a["read"] for a in alerts),
                "source_limit": 100,
            }
        )

    def post(self, request):
        serializer = ReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org = self.organization()
        valid = {alert["id"] for alert in live_alerts(org)} if org else set()
        ids = set(serializer.validated_data["ids"])
        if not ids <= valid:
            raise serializers.ValidationError({"ids": ["Select current alerts in this workspace."]})
        NotificationRead.objects.bulk_create(
            [NotificationRead(organization=org, user=request.user, key=key) for key in ids],
            ignore_conflicts=True,
        )
        return Response({"marked_read": len(ids)})
