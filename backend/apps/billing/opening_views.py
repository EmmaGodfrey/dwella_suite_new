"""Opening balances API: one bounded page of existing tenancies at a time."""

from django.db import transaction
from django.db.models import Exists, OuterRef, Prefetch, Q, Sum
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.common.pagination import StandardPageNumberPagination
from apps.common.permissions import CanManagePortfolio, CanViewPortfolio
from apps.common.property_scope import noted
from apps.common.workspaces import resolve_workspace
from apps.leases.models import Lease

from . import opening
from .models import DepositEntry, Invoice

MAX_ROWS = 25
MONEY = {"max_digits": 12, "decimal_places": 2}


class OpeningWriteThrottle(UserRateThrottle):
    scope = "opening_balance_write"
    rate = "60/hour"


class RowSerializer(serializers.Serializer):
    lease = serializers.UUIDField()
    owes = serializers.DecimalField(required=False, allow_null=True, **MONEY)
    owed_since = serializers.DateField(required=False, allow_null=True)
    # Absent leaves it alone; null bills every month again.
    rent_paid_up_to = serializers.DateField(required=False, allow_null=True)
    deposit_held = serializers.DecimalField(required=False, allow_null=True, **MONEY)


class BatchSerializer(serializers.Serializer):
    as_of = serializers.DateField(default=timezone.localdate)
    rows = RowSerializer(many=True, allow_empty=False, max_length=MAX_ROWS)

    def validate_as_of(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("The date cannot be in the future.")
        return value

    def validate_rows(self, rows):
        leases = [row["lease"] for row in rows]
        if len(set(leases)) != len(leases):
            raise serializers.ValidationError("Each lease can only appear once.")
        return rows


def leases(request):
    return (
        Lease.objects.for_request(request)
        .filter(status=Lease.Status.ACTIVE)
        .select_related("tenant", "unit__property")
    )


def row_data(lease):
    balance = lease.opening_invoices[0] if lease.opening_invoices else None
    paid_up_to = opening.rent_paid_up_to(lease)
    return {
        "lease": str(lease.public_id),
        "reference": lease.reference,
        "tenant": lease.tenant.full_name,
        "premises": f"{lease.unit.property.name} · {lease.unit.name}",
        "monthly_rent": f"{lease.monthly_rent:.2f}",
        "rent_due_day": lease.rent_due_day,
        "end_date": lease.end_date.isoformat(),
        "deposit_agreed": f"{lease.deposit_amount:.2f}",
        "deposit_held": f"{lease.deposit_recorded or 0:.2f}",
        "rent_paid_up_to": paid_up_to.isoformat() if paid_up_to else None,
        "opening_balance": (
            {
                "invoice": str(balance.public_id),
                "reference": balance.reference,
                "owed": f"{balance.total:.2f}",
                "balance": f"{balance.balance:.2f}",
                "owed_since": balance.due_date.isoformat(),
                "status": balance.status,
            }
            if balance
            else None
        ),
    }


class OpeningBalancesView(APIView):
    def get_permissions(self):
        allowed = CanViewPortfolio if self.request.method in SAFE_METHODS else CanManagePortfolio
        return [allowed()]

    def get_throttles(self):
        if self.request.method in SAFE_METHODS:
            return super().get_throttles()
        return [OpeningWriteThrottle()]

    def get(self, request):
        balances = Invoice.objects.filter(is_opening_balance=True).exclude(
            status=Invoice.Status.VOID
        )
        rows = (
            leases(request)
            .prefetch_related(Prefetch("invoices", queryset=balances, to_attr="opening_invoices"))
            .annotate(deposit_recorded=Sum("deposit_entries__amount"))
            .order_by("tenant__full_name", "pk")
        )
        search = request.query_params.get("search", "").strip()[:100]
        if search:
            rows = rows.filter(
                Q(tenant__full_name__icontains=search)
                | Q(unit__name__icontains=search)
                | Q(unit__property__name__icontains=search)
                | Q(reference__icontains=search)
            )
        # Still waiting: nothing recorded yet for this tenancy.
        if request.query_params.get("pending") == "true":
            rows = rows.filter(
                ~Exists(balances.filter(lease=OuterRef("pk"))),
                ~Exists(DepositEntry.objects.filter(lease=OuterRef("pk"))),
                billed_from__isnull=True,
            )
        paginator = StandardPageNumberPagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response([row_data(lease) for lease in page])

    def post(self, request):
        serializer = BatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        as_of, rows = serializer.validated_data["as_of"], serializer.validated_data["rows"]
        organization = resolve_workspace(request)
        found = {
            lease.public_id: lease
            for lease in leases(request).filter(
                public_id__in=[row["lease"] for row in rows]
            )
        }
        errors = {}
        # All or nothing: a bad row is reported and the whole page can be resent.
        with transaction.atomic():
            # A consistent lock order, so two batches cannot deadlock.
            numbered = sorted(
                enumerate(rows),
                key=lambda item: found[item[1]["lease"]].pk if item[1]["lease"] in found else 0,
            )
            for index, row in numbered:
                try:
                    with transaction.atomic():
                        self.apply(request, organization, found.get(row["lease"]), row, as_of)
                except ValidationError as error:
                    errors[str(index)] = error.detail
            if errors:
                raise ValidationError({"rows": errors})
        return Response({"saved": len(rows)})

    def apply(self, request, organization, lease, row, as_of):
        if lease is None:
            raise ValidationError({"lease": ["This lease is not active in this workspace."]})
        noted(request, lease)
        if row.get("owes") is not None:
            invoice = opening.record_opening_balance(
                lease, amount=row["owes"], owed_since=row.get("owed_since") or as_of
            )
            record_event(
                request, "billing.opening_balance_recorded", invoice, organization,
                amount=str(invoice.total),
            )
        if "rent_paid_up_to" in row:
            updated = opening.set_rent_paid_up_to(lease, row["rent_paid_up_to"])
            record_event(
                request, "billing.rent_paid_up_to_set", updated, organization,
                billed_from=str(updated.billed_from or ""),
            )
        if row.get("deposit_held") is not None:
            entry = opening.record_deposit_held(
                lease, amount=row["deposit_held"], occurred_on=as_of, user=request.user
            )
            record_event(
                request, "deposit.opening_recorded", entry, organization, amount=str(entry.amount)
            )
