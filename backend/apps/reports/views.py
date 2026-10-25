import csv
from datetime import timedelta
from decimal import Decimal
from io import StringIO

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
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Invoice
from apps.common.permissions import CanViewPortfolio
from apps.common.workspaces import resolve_workspace
from apps.leases.models import Lease
from apps.properties.models import Property, Unit


class ReportParameters(serializers.Serializer):
    property = serializers.UUIDField(required=False)
    export = serializers.ChoiceField(choices=["csv"], required=False)
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=25)


def csv_cell(value):
    text = str(value if value is not None else "")
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else text


class PortfolioReportView(APIView):
    permission_classes = [IsAuthenticated, CanViewPortfolio]
    report = "rent-roll"

    def get(self, request):
        params = ReportParameters(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data
        org = resolve_workspace(request)
        property_id = data.get("property")
        if (
            property_id
            and not Property.objects.for_organization(org).filter(public_id=property_id).exists()
        ):
            raise serializers.ValidationError(
                {"property": ["Select a property in this workspace."]}
            )
        today = timezone.localdate()
        report = self.arrears if self.report == "arrears" else self.rent_roll
        queryset, totals = report(org, property_id, today)
        if data.get("export") == "csv":
            response = StreamingHttpResponse(
                self.csv_lines(queryset, today), content_type="text/csv; charset=utf-8"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="dwella-{self.report}-{today}.csv"'
            )
            return response
        size, page = data["page_size"], data["page"]
        count = totals["invoices" if self.report == "arrears" else "units"]
        pages = max(1, (count + size - 1) // size)
        if page > pages:
            raise serializers.ValidationError({"page": ["This page does not exist."]})
        rows = queryset[(page - 1) * size : page * size]
        return Response(
            {
                "rows": [self.row(item, today) for item in rows],
                "totals": totals,
                "as_of": today,
                "currency": org.currency if org else "ZMW",
                "page": page,
                "total_rows": count,
                "total_pages": pages,
            }
        )

    def csv_lines(self, queryset, today):
        """Write the export a chunk of rows at a time instead of holding it all."""
        buffer = StringIO(newline="")
        writer = csv.writer(buffer)
        headers = HEADERS[self.report]

        def take():
            value = buffer.getvalue()
            buffer.seek(0)
            buffer.truncate()
            return value

        writer.writerow(headers)
        yield "﻿" + take()
        for item in queryset.iterator(chunk_size=500):
            row = self.row(item, today)
            writer.writerow([csv_cell(row.get(key)) for key in headers])
            yield take()

    def row(self, item, today):
        return arrears_row(item, today) if self.report == "arrears" else rent_roll_row(item)

    def rent_roll(self, org, property_id, today):
        """Units with their unpaid balance; totals are added up by the database."""
        unpaid = Invoice.objects.for_organization(org).filter(status__in=Invoice.UNPAID_STATUSES)
        units = Unit.objects.for_organization(org)
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
        invoices = Invoice.objects.for_organization(org).filter(
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
HEADERS = {
    "arrears": [
        "invoice", "invoice_id", "tenant", "property", "unit", "due_date", "days_overdue",
        "balance",
    ],
    "rent-roll": [
        "property", "unit", "tenant", "status", "monthly_rent", "balance", "rent_due_day",
        "lease_id", "lease_end",
    ],
}


def money(value):
    return f"{value or Decimal(0):.2f}"


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
