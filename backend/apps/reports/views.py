import csv
from decimal import Decimal
from io import StringIO

from django.db.models import Prefetch
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Invoice
from apps.common.permissions import CanViewPortfolio, get_active_membership
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
        membership = get_active_membership(request.user)
        org = membership.organization if membership else None
        property_id = data.get("property")
        if (
            property_id
            and not Property.objects.for_organization(org).filter(public_id=property_id).exists()
        ):
            raise serializers.ValidationError(
                {"property": ["Select a property in this workspace."]}
            )
        today = timezone.localdate()
        rows, totals = (
            self.arrears(org, property_id, today)
            if self.report == "arrears"
            else self.rent_roll(org, property_id, today)
        )
        if data.get("export") == "csv":
            stream = StringIO(newline="")
            stream.write("\ufeff")
            writer = csv.writer(stream)
            headers = (
                list(rows[0])
                if rows
                else (
                    ["invoice", "tenant", "property", "unit", "due_date", "days_overdue", "balance"]
                    if self.report == "arrears"
                    else ["property", "unit", "tenant", "status", "monthly_rent", "balance"]
                )
            )
            writer.writerow(headers)
            for row in rows:
                writer.writerow([csv_cell(row.get(key)) for key in headers])
            response = HttpResponse(stream.getvalue(), content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = (
                f'attachment; filename="dwella-{self.report}-{today}.csv"'
            )
            return response
        size, page = data["page_size"], data["page"]
        pages = max(1, (len(rows) + size - 1) // size)
        if page > pages:
            raise serializers.ValidationError({"page": ["This page does not exist."]})
        return Response(
            {
                "rows": rows[(page - 1) * size : page * size],
                "totals": totals,
                "as_of": today,
                "currency": org.currency if org else "ZMW",
                "page": page,
                "total_rows": len(rows),
                "total_pages": pages,
            }
        )

    def rent_roll(self, org, property_id, today):
        units = (
            Unit.objects.for_organization(org)
            .select_related("property")
            .prefetch_related(
                Prefetch(
                    "leases",
                    queryset=Lease.objects.for_organization(org)
                    .filter(status=Lease.Status.ACTIVE)
                    .select_related("tenant"),
                    to_attr="active_leases",
                ),
                Prefetch(
                    "invoices",
                    queryset=Invoice.objects.for_organization(org).filter(
                        status__in=Invoice.UNPAID_STATUSES
                    ),
                    to_attr="unpaid_invoices",
                ),
            )
        )
        if property_id:
            units = units.filter(property__public_id=property_id)
        rows = []
        rent, balance, occupied = Decimal(0), Decimal(0), 0
        for unit in units:
            lease = unit.active_leases[0] if unit.active_leases else None
            monthly = lease.monthly_rent if lease else Decimal(0)
            owed = sum((invoice.balance for invoice in unit.unpaid_invoices), Decimal(0))
            occupied += bool(lease)
            rent += monthly
            balance += owed
            rows.append(
                {
                    "property": unit.property.name,
                    "unit": unit.name,
                    "tenant": lease.tenant.full_name if lease else "",
                    "status": "occupied" if lease else unit.occupancy_status,
                    "monthly_rent": f"{monthly:.2f}",
                    "balance": f"{owed:.2f}",
                    "rent_due_day": lease.rent_due_day if lease else None,
                    "lease_id": str(lease.public_id) if lease else None,
                    "lease_end": lease.end_date.isoformat() if lease else None,
                }
            )
        return rows, {
            "units": len(rows),
            "occupied": occupied,
            "monthly_rent": f"{rent:.2f}",
            "balance": f"{balance:.2f}",
        }

    def arrears(self, org, property_id, today):
        invoices = (
            Invoice.objects.for_organization(org)
            .filter(status__in=Invoice.UNPAID_STATUSES, due_date__lt=today)
            .select_related("tenant", "unit__property")
            .order_by("due_date", "reference")
        )
        if property_id:
            invoices = invoices.filter(unit__property__public_id=property_id)
        totals = {
            "balance": Decimal(0),
            "days_1_30": Decimal(0),
            "days_31_60": Decimal(0),
            "days_61_90": Decimal(0),
            "days_91_plus": Decimal(0),
        }
        rows = []
        for invoice in invoices:
            age = (today - invoice.due_date).days
            bucket = (
                "days_1_30"
                if age <= 30
                else "days_31_60"
                if age <= 60
                else "days_61_90"
                if age <= 90
                else "days_91_plus"
            )
            totals[bucket] += invoice.balance
            totals["balance"] += invoice.balance
            rows.append(
                {
                    "invoice": invoice.reference,
                    "invoice_id": str(invoice.public_id),
                    "tenant": invoice.tenant.full_name,
                    "property": invoice.unit.property.name if invoice.unit else "Unassigned",
                    "unit": invoice.unit.name if invoice.unit else "",
                    "due_date": invoice.due_date.isoformat(),
                    "days_overdue": age,
                    "balance": f"{invoice.balance:.2f}",
                }
            )
        return rows, {
            **{key: f"{value:.2f}" for key, value in totals.items()},
            "invoices": len(rows),
        }
