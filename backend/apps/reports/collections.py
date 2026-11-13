from django.db.models import Count, F, Q, Sum

from apps.billing.models import Payment
from apps.common.property_scope import property_scope
from apps.common.workspaces import resolve_workspace

from .common import (
    ReportView,
    csv_response,
    money,
    organization_today,
    page_bounds,
    report_response,
    validate_scope,
)
from .serializers import CollectionParameters

COLLECTION_BASIS = (
    "Gross recorded payments, using their payment dates and current corrections. "
    "Reversed payments and void invoices are excluded. This is not net settlement."
)
COLLECTION_HEADERS = [
    "receipt", "paid_on", "tenant", "property", "unit", "invoice", "method", "amount",
    "currency", "date_from", "date_to", "basis",
]


class CollectionsReportView(ReportView):
    def get(self, request):
        org = resolve_workspace(request)
        today = organization_today(org)
        params = CollectionParameters(data=request.query_params, context={"today": today})
        params.is_valid(raise_exception=True)
        data = params.validated_data
        scope = property_scope(request)
        tenant = validate_scope(org, data, scope)
        payments = scope.filter(Payment.objects.for_organization(org)).filter(
            reversed_at__isnull=True,
            invoice__organization=org,
            invoice__tenant_id=F("tenant_id"),
            tenant__organization=org,
            paid_on__range=(data["date_from"], data["date_to"]),
        ).exclude(invoice__status="void")
        if tenant:
            payments = payments.filter(tenant=tenant)
        if data.get("property"):
            payments = payments.filter(invoice__unit__property__public_id=data["property"])
        if data.get("method"):
            payments = payments.filter(method=data["method"])
        sums = payments.aggregate(
            payments=Count("pk"), gross=Sum("amount"),
            **{method: Sum("amount", filter=Q(method=method)) for method in Payment.Method.values},
        )
        rows = payments.order_by("-paid_on", "-pk").values(
            "public_id", "receipt_number", "paid_on", "method", "amount", "tenant__full_name",
            "tenant__public_id", "invoice__reference", "invoice__public_id",
            "invoice__unit__name", "invoice__unit__property__name",
        )

        def render(item):
            return {
                "id": str(item["public_id"]),
                "receipt": item["receipt_number"],
                "paid_on": item["paid_on"].isoformat(),
                "tenant": item["tenant__full_name"],
                "tenant_id": str(item["tenant__public_id"]),
                "property": item["invoice__unit__property__name"] or "Unassigned",
                "unit": item["invoice__unit__name"] or "",
                "invoice": item["invoice__reference"],
                "invoice_id": str(item["invoice__public_id"]),
                "method": item["method"],
                "amount": money(item["amount"]),
                "currency": org.currency,
                "date_from": data["date_from"].isoformat(),
                "date_to": data["date_to"].isoformat(),
                "basis": COLLECTION_BASIS,
            }

        if data.get("export") == "csv":
            return csv_response(
                f"dwella-collections-{data['date_from']}-{data['date_to']}",
                COLLECTION_HEADERS,
                (render(item) for item in rows.iterator(chunk_size=500)),
                numeric_columns={"amount"},
            )
        offset, size, _, _ = page_bounds(data, sums["payments"])
        return report_response(request, data, sums["payments"], {
            "rows": [render(item) for item in rows[offset:offset + size]],
            "totals": {"payments": sums["payments"], "amount": money(sums["gross"])},
            "by_method": {method: money(sums[method]) for method in Payment.Method.values},
            "date_from": data["date_from"],
            "date_to": data["date_to"],
            "as_of": today,
            "currency": org.currency,
            "basis": COLLECTION_BASIS,
        })
