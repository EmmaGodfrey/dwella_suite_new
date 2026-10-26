from datetime import timedelta

from django.db.models import Exists, OuterRef
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.billing.models import Invoice, Payment
from apps.common.permissions import CanViewPortfolio
from apps.common.workspaces import resolve_workspace
from apps.leases.models import Lease
from apps.maintenance.models import MaintenanceRequest
from apps.payments.models import Payout
from apps.portal.access import portal_context

from .models import NotificationPreferences, NotificationRead
from .tenant_alerts import tenant_alerts


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
        # A renewal in progress already answers "this lease ends soon".
        .exclude(
            Exists(Lease.objects.filter(renewal_of=OuterRef("pk"), status__in=Lease.OPEN_STATUSES))
        )
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
    for lease in (
        Lease.objects.for_organization(org)
        .filter(
            renewal_of__isnull=False,
            status__in=(Lease.Status.DRAFT, Lease.Status.PENDING_SIGNATURE),
            start_date__lte=today,
        )
        .select_related("tenant", "unit")
        .order_by("start_date", "pk")[:100]
    ):
        # Signed renewals start on their own; these still need signing or starting.
        alerts.append(
            {
                "id": f"renewal:{lease.public_id}:{lease.start_date}",
                "kind": "lease",
                "title": f"{lease.reference} renewal has not started",
                "body": f"{lease.tenant.full_name} · {lease.unit.name}",
                "path": f"/leases/{lease.public_id}",
                "date": lease.start_date.isoformat(),
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
    for payout in (
        Payout.objects.filter(
            collection__organization=org,
            status__in=["failed", "review"],
        )
        .select_related("collection__invoice")
        .order_by("-updated_at")[:100]
    ):
        alerts.append(
            {
                "id": f"payout:{payout.public_id}:{payout.status}",
                "kind": "payment",
                "title": "Landlord payout needs attention",
                "body": (
                    f"{payout.collection.invoice.reference} · The rent payment remains recorded."
                ),
                "path": f"/billing/invoices/{payout.collection.invoice.public_id}",
                "date": timezone.localtime(payout.updated_at).date().isoformat(),
            }
        )
    return sorted(alerts, key=lambda alert: (alert["date"], alert["id"]))


class ReadSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.CharField(max_length=100), min_length=1, max_length=1000
    )


class CanViewNotifications(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if CanViewPortfolio().has_permission(request, view):
            return True
        request.tenant_notification_context = portal_context(request)
        return True


class NotificationReadThrottle(UserRateThrottle):
    scope = "notification_read"
    rate = "120/hour"


class NotificationsView(APIView):
    permission_classes = [IsAuthenticated, CanViewNotifications]

    def get_throttles(self):
        return (
            [NotificationReadThrottle()]
            if self.request.method == "POST"
            else super().get_throttles()
        )

    def alerts(self, request):
        portal = getattr(request, "tenant_notification_context", None)
        return tenant_alerts(portal, request.user) if portal else live_alerts(self.organization())

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response

    def organization(self):
        return resolve_workspace(self.request)

    def get(self, request):
        org = self.organization()
        alerts = self.alerts(request)
        preferences = NotificationPreferences.objects.filter(user=request.user).first()
        if preferences:
            categories = {
                "payment": "payment",
                "invoice": "payment",
                "payout": "payout",
                "lease": "lease",
                "renewal": "lease",
                "repair": "maintenance",
                "repair_update": "maintenance",
                "document": "lease",
            }

            def enabled(alert):
                if alert["kind"] == "arrears":
                    return True
                category = categories.get(alert["id"].split(":")[0])
                return category is None or getattr(preferences, f"in_app_{category}", True)

            alerts = [alert for alert in alerts if enabled(alert)]
        read = set(
            NotificationRead.objects.filter(
                organization=org, user=request.user, key__in=[alert["id"] for alert in alerts]
            ).values_list("key", flat=True)
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
        valid = {alert["id"] for alert in self.alerts(request)}
        ids = set(serializer.validated_data["ids"])
        if not ids <= valid:
            raise serializers.ValidationError({"ids": ["Select current alerts in this workspace."]})
        NotificationRead.objects.bulk_create(
            [NotificationRead(organization=org, user=request.user, key=key) for key in ids],
            ignore_conflicts=True,
        )
        return Response({"marked_read": len(ids)})
