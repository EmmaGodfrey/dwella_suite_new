from datetime import timedelta
from decimal import Decimal

from django.db.models import (
    Count,
    DecimalField,
    F,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from apps.billing.models import Invoice
from apps.common.property_scope import property_scope
from apps.common.workspaces import resolve_workspace
from apps.leases.models import Lease
from apps.properties.models import Unit

from .common import (
    ReportView,
    csv_response,
    money,
    organization_today,
    page_bounds,
    report_response,
    validate_scope,
)
from .serializers import ReportParameters


class PortfolioReportView(ReportView):
    report = "rent-roll"

    def get(self, request):
        params = ReportParameters(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data
        org = resolve_workspace(request)
        property_id = data.get("property")
        self.scope = property_scope(request)
        validate_scope(org, data, self.scope)
        today = organization_today(org)
        report = self.arrears if self.report == "arrears" else self.rent_roll
        queryset, totals = report(org, property_id, today)
        metadata = {
            "as_of": today.isoformat(), "currency": org.currency,
            "basis": BASES[self.report],
        }
        if data.get("export") == "csv":
            return csv_response(
                f"dwella-{self.report}-{today}", HEADERS[self.report],
                ({**self.row(item, today), **metadata}
                 for item in queryset.iterator(chunk_size=500)),
                numeric_columns={"balance", "monthly_rent"} & set(HEADERS[self.report]),
            )
        count = totals["invoices" if self.report == "arrears" else "units"]
        offset, size, _, _ = page_bounds(data, count)
        rows = queryset[offset:offset + size]
        return report_response(request, data, count, {
            "rows": [self.row(item, today) for item in rows],
            "totals": totals,
            "as_of": today,
            "currency": org.currency if org else "ZMW",
            "basis": BASES[self.report],
        })

    def row(self, item, today):
        return arrears_row(item, today) if self.report == "arrears" else rent_roll_row(item)

    def rent_roll(self, org, property_id, today):
        """Units with their unpaid balance; totals are added up by the database."""
        unpaid = self.scope.filter(Invoice.objects.for_organization(org)).filter(
            status__in=Invoice.UNPAID_STATUSES
        )
        units = self.scope.filter(Unit.objects.for_organization(org))
        if property_id:
            units = units.filter(property__public_id=property_id)
        owed = (
            unpaid.filter(unit=OuterRef("pk"))
            .order_by()
            .values("unit")
            .annotate(total=Sum(F("total") - F("amount_paid")))
            .values("total")
        )
        queryset = (
            units.select_related("property")
            .annotate(owed=Coalesce(Subquery(owed), ZERO))
            .prefetch_related(
                Prefetch(
                    "leases",
                    queryset=Lease.objects.for_organization(org)
                    .filter(status=Lease.Status.ACTIVE)
                    .select_related("tenant"),
                    to_attr="active_leases",
                )
            )
            .order_by("property__name", "name", "id")
        )
        leases = Lease.objects.for_organization(org).filter(
            status=Lease.Status.ACTIVE, unit__in=units
        ).aggregate(occupied=Count("id"), rent=Sum("monthly_rent"))
        balance = unpaid.filter(unit__in=units).aggregate(
            total=Sum(F("total") - F("amount_paid"))
        )["total"]
        return queryset, {
            "units": units.count(),
            "occupied": leases["occupied"],
            "monthly_rent": money(leases["rent"]),
            "balance": money(balance),
        }

    def arrears(self, org, property_id, today):
        """Overdue invoices, oldest first; each age band is summed by the database."""
        invoices = self.scope.filter(Invoice.objects.for_organization(org)).filter(
            status__in=Invoice.UNPAID_STATUSES, due_date__lt=today
        )
        if property_id:
            invoices = invoices.filter(unit__property__public_id=property_id)
        owed = F("total") - F("amount_paid")
        bands = {
            "days_1_30": Q(due_date__gte=today - timedelta(days=30)),
            "days_31_60": Q(
                due_date__lt=today - timedelta(days=30), due_date__gte=today - timedelta(days=60)
            ),
            "days_61_90": Q(
                due_date__lt=today - timedelta(days=60), due_date__gte=today - timedelta(days=90)
            ),
            "days_91_plus": Q(due_date__lt=today - timedelta(days=90)),
        }
        sums = invoices.aggregate(
            invoices=Count("id"),
            balance=Sum(owed),
            **{key: Sum(owed, filter=band) for key, band in bands.items()},
        )
        totals = {key: money(sums[key]) for key in ["balance", *bands]}
        totals["invoices"] = sums["invoices"]
        queryset = invoices.select_related("tenant", "unit__property").order_by(
            "due_date", "reference"
        )
        return queryset, totals


ZERO = Value(Decimal(0), output_field=DecimalField(max_digits=12, decimal_places=2))
BASES = {
    "rent-roll": (
        "Current active leases and unit balances. Outstanding includes invoices for current "
        "and previous tenants; it is not solely the current tenant's debt."
    ),
    "arrears": (
        "Current unpaid invoices past their due date, including rent and other charges. "
        "Invoices due today are not overdue. This is not a historical snapshot."
    ),
}
HEADERS = {
    "arrears": [
        "invoice", "invoice_id", "tenant", "property", "unit", "due_date", "days_overdue",
        "balance", "currency", "as_of", "basis",
    ],
    "rent-roll": [
        "property", "unit", "tenant", "status", "monthly_rent", "balance", "rent_due_day",
        "lease_id", "lease_end", "currency", "as_of", "basis",
    ],
}


def rent_roll_row(unit):
    lease = unit.active_leases[0] if unit.active_leases else None
    return {
        "property": unit.property.name,
        "unit": unit.name,
        "tenant": lease.tenant.full_name if lease else "",
        "status": "occupied" if lease else unit.occupancy_status,
        "monthly_rent": money(lease.monthly_rent if lease else None),
        "balance": money(unit.owed),
        "rent_due_day": lease.rent_due_day if lease else None,
        "lease_id": str(lease.public_id) if lease else None,
        "lease_end": lease.end_date.isoformat() if lease else None,
    }


def arrears_row(invoice, today):
    return {
        "invoice": invoice.reference,
        "invoice_id": str(invoice.public_id),
        "tenant": invoice.tenant.full_name,
        "property": invoice.unit.property.name if invoice.unit else "Unassigned",
        "unit": invoice.unit.name if invoice.unit else "",
        "due_date": invoice.due_date.isoformat(),
        "days_overdue": (today - invoice.due_date).days,
        "balance": money(invoice.balance),
    }
