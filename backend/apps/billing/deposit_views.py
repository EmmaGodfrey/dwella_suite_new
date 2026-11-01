"""Security deposit API for property managers and tenants."""

from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.common.permissions import CanManagePortfolio, CanViewPortfolio
from apps.common.workspaces import resolve_workspace
from apps.leases.models import Lease
from apps.portal.access import IsPortalTenant, portal_context

from . import deposits
from .models import DepositDeduction, DepositEvidence, Payment

MONEY = {"max_digits": 12, "decimal_places": 2}


def money(value):
    return f"{Decimal(value):.2f}"


class DepositWriteThrottle(UserRateThrottle):
    scope = "deposit_write"
    rate = "60/hour"


def deduction_data(row, *, tenant=False):
    data = {
        "id": str(row.public_id),
        "amount": money(row.amount),
        "reason": row.reason,
        "details": row.details,
        "status": row.status,
        "status_label": row.get_status_display(),
        "proposed_on": row.created_at.date().isoformat(),
        "tenant_note": row.tenant_note,
        "responded_at": row.responded_at,
        "resolution_note": row.resolution_note,
        "decided_at": row.decided_at,
        "evidence": [
            {
                "id": str(item.public_id),
                "name": item.name,
                "content_type": item.content_type,
                "size": item.size,
            }
            for item in row.evidence.all()
        ],
    }
    if tenant:
        data["can_respond"] = row.status in DepositDeduction.OPEN_STATUSES
    return data


def payload(lease, *, tenant=False):
    info = deposits.summary(lease)
    rows = info["deductions"]
    if tenant:
        rows = [row for row in rows if row.status != DepositDeduction.Status.WITHDRAWN]
    return {
        "lease": {
            "id": str(lease.public_id),
            "reference": lease.reference,
            "status": lease.status,
            "tenant": lease.tenant.full_name,
            "premises": f"{lease.unit.property.name} · {lease.unit.name}",
        },
        **{
            key: money(info[key])
            for key in ("agreed", "held", "collected", "reserved", "available", "requested_unpaid")
        },
        "entries": [
            {
                "id": str(entry.public_id),
                "kind": entry.kind,
                "label": entry.get_kind_display(),
                "amount": money(entry.amount),
                "date": entry.occurred_on.isoformat(),
                "reference": entry.reference,
                "method": entry.get_method_display() if entry.method else "",
                "note": entry.note,
            }
            for entry in info["entries"]
        ],
        "deductions": [deduction_data(row, tenant=tenant) for row in rows],
    }


class ManagerView(APIView):
    def get_permissions(self):
        allowed = CanViewPortfolio if self.request.method in SAFE_METHODS else CanManagePortfolio
        return [allowed()]

    def get_throttles(self):
        if self.request.method in SAFE_METHODS:
            return super().get_throttles()
        return [DepositWriteThrottle()]

    def lease(self, public_id):
        return get_object_or_404(
            Lease.objects.for_organization(resolve_workspace(self.request)).select_related(
                "tenant", "unit__property", "organization"
            ),
            public_id=public_id,
        )

    def deduction(self, public_id):
        return get_object_or_404(
            DepositDeduction.objects.for_organization(
                resolve_workspace(self.request)
            ).select_related("lease__tenant", "lease__unit__property", "lease__organization"),
            public_id=public_id,
        )

    def done(self, lease, action, resource, **meta):
        record_event(self.request, action, resource, lease.organization, **meta)
        return Response(payload(lease))

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


class RequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(required=False, **MONEY)


class OpeningSerializer(serializers.Serializer):
    amount = serializers.DecimalField(**MONEY)
    occurred_on = serializers.DateField()
    note = serializers.CharField(max_length=500, required=False, default="", allow_blank=True)


class DeductionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(**MONEY)
    reason = serializers.CharField(max_length=200)
    details = serializers.CharField(max_length=2000, required=False, default="", allow_blank=True)


class RefundSerializer(serializers.Serializer):
    amount = serializers.DecimalField(**MONEY)
    method = serializers.ChoiceField(choices=Payment.Method.choices)
    reference = serializers.CharField(max_length=100, required=False, default="", allow_blank=True)
    paid_on = serializers.DateField(default=timezone.localdate)
    note = serializers.CharField(max_length=500, required=False, default="", allow_blank=True)


class ResolutionSerializer(serializers.Serializer):
    resolution_note = serializers.CharField(
        max_length=1000, required=False, default="", allow_blank=True
    )


def valid(serializer_class, request):
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


class DepositView(ManagerView):
    def get(self, request, public_id):
        return Response(payload(self.lease(public_id)))


class DepositRequestView(ManagerView):
    def post(self, request, public_id):
        lease = self.lease(public_id)
        invoice = deposits.request_deposit(
            lease, user=request.user, **valid(RequestSerializer, request)
        )
        return self.done(lease, "deposit.requested", invoice, amount=str(invoice.total))


class DepositOpeningView(ManagerView):
    def post(self, request, public_id):
        lease = self.lease(public_id)
        data = valid(OpeningSerializer, request)
        entry = deposits.record_opening(lease, user=request.user, **data)
        return self.done(lease, "deposit.opening_recorded", entry, amount=str(entry.amount))


class DepositDeductionCreateView(ManagerView):
    def post(self, request, public_id):
        lease = self.lease(public_id)
        row = deposits.propose_deduction(
            lease, user=request.user, **valid(DeductionSerializer, request)
        )
        response = self.done(lease, "deposit.deduction_proposed", row, amount=str(row.amount))
        # Lets the screen attach evidence to the deduction it just created.
        response.data["created_id"] = str(row.public_id)
        return response


class DepositRefundView(ManagerView):
    def post(self, request, public_id):
        lease = self.lease(public_id)
        data = valid(RefundSerializer, request)
        entry = deposits.record_refund(lease, user=request.user, **data)
        return self.done(lease, "deposit.refund_recorded", entry, amount=str(-entry.amount))


class DeductionDecisionView(ManagerView):
    def post(self, request, public_id, decision):
        row = self.deduction(public_id)
        if decision == "apply":
            row = deposits.apply_deduction(
                row, user=request.user, **valid(ResolutionSerializer, request)
            )
        elif decision == "withdraw":
            row = deposits.withdraw_deduction(row, user=request.user)
        else:
            from rest_framework.exceptions import NotFound

            raise NotFound()
        return self.done(row.lease, f"deposit.deduction_{row.status}", row)


def evidence_response(item):
    from django.http import HttpResponse

    from apps.documents.views import private_headers

    response = HttpResponse(bytes(item.content), content_type=item.content_type)
    response["Content-Disposition"] = f'attachment; filename="{item.name}"'
    response["Content-Security-Policy"] = "sandbox; default-src 'none'"
    return private_headers(response)


class DeductionEvidenceView(ManagerView):
    def post(self, request, public_id):
        row = self.deduction(public_id)
        item = deposits.add_evidence(row, upload=request.FILES.get("file"), user=request.user)
        return self.done(row.lease, "deposit.evidence_added", item, name=item.name)


class EvidenceFileView(ManagerView):
    def get(self, request, public_id):
        item = get_object_or_404(
            DepositEvidence.objects.for_organization(resolve_workspace(request)),
            public_id=public_id,
        )
        return evidence_response(item)


# Tenant portal


class RespondSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["accept", "dispute"])
    note = serializers.CharField(max_length=1000, required=False, default="", allow_blank=True)


class TenantDepositsView(APIView):
    permission_classes = [IsPortalTenant]

    def get(self, request):
        from apps.portal.views import leases

        rows = leases(portal_context(request)).select_related("tenant", "unit__property")
        # Only tenancies with a deposit agreed or recorded.
        result = [payload(lease, tenant=True) for lease in rows]
        return Response(
            [r for r in result if r["agreed"] != "0.00" or r["entries"] or r["deductions"]]
        )


class TenantDeductionResponseView(APIView):
    permission_classes = [IsPortalTenant]

    def get_throttles(self):
        return [DepositWriteThrottle()]

    def post(self, request, public_id):
        portal = portal_context(request)
        row = get_object_or_404(
            deposits.tenant_visible(
                DepositDeduction.objects.filter(
                    organization=portal.organization, lease__tenant_id__in=portal.tenant_ids
                )
            ).select_related("lease__tenant", "lease__unit__property"),
            public_id=public_id,
        )
        data = valid(RespondSerializer, request)
        row = deposits.respond_to_deduction(
            row, accept=data["decision"] == "accept", note=data["note"]
        )
        record_event(request, f"deposit.deduction_{row.status}", row, portal.organization)
        return Response(payload(row.lease, tenant=True))


class TenantEvidenceFileView(APIView):
    permission_classes = [IsPortalTenant]

    def get(self, request, public_id):
        portal = portal_context(request)
        item = get_object_or_404(
            DepositEvidence.objects.filter(
                organization=portal.organization,
                deduction__lease__tenant_id__in=portal.tenant_ids,
            ).exclude(deduction__status=DepositDeduction.Status.WITHDRAWN),
            public_id=public_id,
        )
        return evidence_response(item)
