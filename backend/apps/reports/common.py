import csv
from decimal import Decimal
from io import StringIO
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.utils.urls import replace_query_param
from rest_framework.views import APIView

from apps.common.permissions import CanViewPortfolio
from apps.common.property_scope import EVERYTHING
from apps.properties.models import Property
from apps.tenants.models import Tenant


class ReportExportThrottle(UserRateThrottle):
    scope = "report_export"
    rate = "30/hour"


class ReportView(APIView):
    permission_classes = [IsAuthenticated, CanViewPortfolio]

    def get_throttles(self):
        throttles = super().get_throttles()
        if self.request.query_params.get("export") == "csv":
            throttles.append(ReportExportThrottle())
        return throttles

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


def organization_today(organization):
    try:
        zone = ZoneInfo(organization.timezone) if organization else timezone.get_current_timezone()
    except ZoneInfoNotFoundError:
        raise serializers.ValidationError(
            "Correct this workspace's timezone before reporting."
        ) from None
    return timezone.localdate(timezone=zone)


def validate_scope(organization, params, scope=EVERYTHING):
    """Check the chosen property and tenant are ones this person may report on."""
    property_id = params.get("property")
    if property_id and not scope.filter(Property.objects.for_organization(organization)).filter(
        public_id=property_id
    ).exists():
        raise serializers.ValidationError({"property": "Select a property in this workspace."})
    tenant = None
    if params.get("tenant"):
        tenant = scope.filter(Tenant.objects.for_organization(organization)).only(
            "id", "public_id", "full_name", "is_active"
        ).filter(public_id=params["tenant"]).first()
        if tenant is None:
            raise serializers.ValidationError({"tenant": "Select a tenant in this workspace."})
    return tenant


def page_bounds(params, count):
    size, page = params["page_size"], params["page"]
    pages = max(1, (count + size - 1) // size)
    if page > pages:
        raise serializers.ValidationError({"page": "This page does not exist."})
    return (page - 1) * size, size, page, pages


def report_response(request, params, count, data):
    _, size, page, pages = page_bounds(params, count)
    url = request.build_absolute_uri()
    # The central renderer owns the envelope; retain existing row metadata too.
    return Response({
        "count": count,
        "page": page,
        "page_size": size,
        "total_pages": pages,
        "next": replace_query_param(url, "page", page + 1) if page < pages else None,
        "previous": replace_query_param(url, "page", page - 1) if page > 1 else None,
        "results": {**data, "page": page, "total_rows": count, "total_pages": pages},
    })


def csv_cell(value):
    if isinstance(value, Decimal | int):
        return str(value)
    text = str(value if value is not None else "")
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else text


def csv_response(filename, headers, rows, *, numeric_columns=()):
    def lines():
        buffer = StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(headers)
        yield "\ufeff" + buffer.getvalue()
        for row in rows:
            buffer.seek(0)
            buffer.truncate()
            writer.writerow([
                csv_cell(Decimal(row[key]) if key in numeric_columns else row.get(key))
                for key in headers
            ])
            yield buffer.getvalue()

    response = StreamingHttpResponse(lines(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
    return response


def money(value):
    return f"{value or Decimal(0):.2f}"
