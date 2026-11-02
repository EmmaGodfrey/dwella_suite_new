"""Payment proof API: tenants report direct payments, managers confirm them."""

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.common.permissions import CanManagePortfolio, CanViewPortfolio
from apps.common.workspaces import resolve_workspace
from apps.portal.access import IsPortalTenant, portal_context

from . import proofs
from .deposit_views import evidence_response
from .models import PaymentProof, PaymentProofFile

MONEY = {"max_digits": 12, "decimal_places": 2}


class ProofWriteThrottle(UserRateThrottle):
    scope = "payment_proof_write"
    rate = "30/hour"


def proof_data(proof, *, tenant=False):
    invoice = proof.invoice
    data = {
        "id": str(proof.public_id),
        "number": proof.number,
        "status": proof.status,
        "status_label": proof.get_status_display(),
        "amount": f"{proof.amount:.2f}",
        "method": proof.method,
        "method_label": proof.get_method_display(),
        "paid_on": proof.paid_on.isoformat(),
        "reference": proof.reference,
        "note": proof.note,
        "submitted_at": proof.submitted_at,
        "revision": proof.revision,
        "review_note": proof.review_note,
        "reviewed_at": proof.reviewed_at,
        "invoice": {
            "id": str(invoice.public_id),
            "reference": invoice.reference,
            "period": invoice.period_start.isoformat() if invoice.period_start else None,
            "balance": f"{invoice.balance:.2f}",
        },
        "receipt": (
            {"id": str(proof.payment.public_id), "number": proof.payment.receipt_number}
            if proof.payment_id
            else None
        ),
        "files": [
            {
                "id": str(item.public_id),
                "name": item.name,
                "content_type": item.content_type,
                "size": item.size,
                "revision": item.revision,
            }
            for item in proof.files.all()
        ],
        "history": proof.history,
    }
    if tenant:
        data["can_cancel"] = proof.status in PaymentProof.OPEN_STATUSES
        data["can_resend"] = proof.status == PaymentProof.Status.NEEDS_INFORMATION
    else:
        unit = invoice.unit
        data["tenant"] = {"id": str(proof.tenant.public_id), "name": proof.tenant.full_name}
        data["premises"] = f"{unit.property.name} · {unit.name}" if unit else ""
        data["can_review"] = proof.status == PaymentProof.Status.SUBMITTED
        # Same file seen on another proof: a warning for the reviewer, not proof of fraud.
        data["possible_duplicates"] = sorted(
            {
                other
                for item in proof.files.all()
                for other in getattr(item, "duplicates", [])
                if other != proof.number
            }
        )
    return data


def with_details(queryset):
    return queryset.select_related(
        "invoice__unit__property", "tenant", "payment"
    ).prefetch_related(Prefetch("files", queryset=PaymentProofFile.objects.defer("content")))


def mark_duplicates(rows):
    """Attach other proofs in the workspace that carry the same file."""
    digests = {item.sha256 for row in rows for item in row.files.all()}
    if not digests:
        return rows
    owners = {}
    for sha, number in PaymentProofFile.objects.filter(
        organization_id=rows[0].organization_id, sha256__in=digests
    ).values_list("sha256", "proof__number"):
        owners.setdefault(sha, set()).add(number)
    for row in rows:
        for item in row.files.all():
            item.duplicates = owners.get(item.sha256, set())
    return rows


class ProofFields(serializers.Serializer):
    amount = serializers.DecimalField(**MONEY)
    method = serializers.ChoiceField(choices=PaymentProof.METHODS)
    paid_on = serializers.DateField()
    reference = serializers.CharField(max_length=80, required=False, default="", allow_blank=True)
    note = serializers.CharField(max_length=1000, required=False, default="", allow_blank=True)


class SubmitSerializer(ProofFields):
    invoice = serializers.UUIDField()


class ReviewSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=1000, required=False, default="", allow_blank=True)


def valid(serializer_class, request):
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def private(response):
    response["Cache-Control"] = "private, no-store"
    return response


# Property manager


class ManagerProofView(APIView):
    def get_permissions(self):
        allowed = CanViewPortfolio if self.request.method in SAFE_METHODS else CanManagePortfolio
        return [allowed()]

    def get_throttles(self):
        if self.request.method in SAFE_METHODS:
            return super().get_throttles()
        return [ProofWriteThrottle()]

    def queryset(self):
        return PaymentProof.objects.for_organization(resolve_workspace(self.request))

    def finalize_response(self, request, response, *args, **kwargs):
        return private(super().finalize_response(request, response, *args, **kwargs))


class ManagerProofListView(ManagerProofView):
    LIMIT = 100

    def get(self, request):
        rows = self.queryset()
        status = request.query_params.get("status")
        if status == "open":
            rows = rows.filter(status=PaymentProof.Status.SUBMITTED)
        elif status in PaymentProof.Status.values:
            rows = rows.filter(status=status)
        invoice = request.query_params.get("invoice")
        if invoice:
            rows = rows.filter(invoice__public_id=invoice)
        waiting = self.queryset().filter(status=PaymentProof.Status.SUBMITTED).count()
        rows = mark_duplicates(list(with_details(rows)[: self.LIMIT]))
        return Response({"waiting": waiting, "results": [proof_data(row) for row in rows]})


class ManagerProofDetailView(ManagerProofView):
    def get(self, request, public_id):
        row = get_object_or_404(with_details(self.queryset()), public_id=public_id)
        return Response(proof_data(mark_duplicates([row])[0]))


class ManagerProofDecisionView(ManagerProofView):
    def post(self, request, public_id, decision):
        row = get_object_or_404(self.queryset(), public_id=public_id)
        note = valid(ReviewSerializer, request)["note"]
        if decision == "confirm":
            row = proofs.confirm(row, user=request.user)
        elif decision in ("reject", "ask"):
            row = proofs.decline(row, user=request.user, note=note, ask=decision == "ask")
        else:
            raise NotFound()
        record_event(
            request, f"payment_proof.{row.status}", row, row.organization, amount=str(row.amount)
        )
        row = with_details(self.queryset()).get(pk=row.pk)
        return Response(proof_data(mark_duplicates([row])[0]))


class ManagerProofFileView(ManagerProofView):
    def get(self, request, public_id):
        item = get_object_or_404(
            PaymentProofFile.objects.for_organization(resolve_workspace(request)),
            public_id=public_id,
        )
        return evidence_response(item)


# Tenant portal


class TenantProofView(APIView):
    permission_classes = [IsPortalTenant]

    def get_throttles(self):
        if self.request.method in SAFE_METHODS:
            return super().get_throttles()
        return [ProofWriteThrottle()]

    def finalize_response(self, request, response, *args, **kwargs):
        return private(super().finalize_response(request, response, *args, **kwargs))

    def queryset(self):
        return portal_context(self.request).scope(PaymentProof.objects.all())

    def mine(self, public_id):
        return get_object_or_404(with_details(self.queryset()), public_id=public_id)


def uploads(request):
    return request.FILES.getlist("files")


class TenantProofListView(TenantProofView):
    def get(self, request):
        rows = with_details(self.queryset())[:50]
        return Response([proof_data(row, tenant=True) for row in rows])

    def post(self, request):
        from apps.portal.views import invoices

        data = valid(SubmitSerializer, request)
        invoice = get_object_or_404(
            invoices(portal_context(request)), public_id=data.pop("invoice")
        )
        row = proofs.submit(invoice, user=request.user, uploads=uploads(request), **data)
        record_event(
            request, "payment_proof.submitted", row, row.organization, amount=str(row.amount)
        )
        return Response(proof_data(self.mine(row.public_id), tenant=True), status=201)


class TenantProofActionView(TenantProofView):
    def post(self, request, public_id, operation):
        row = self.mine(public_id)
        if operation == "cancel":
            row = proofs.cancel(row, user=request.user)
        elif operation == "resend":
            row = proofs.resubmit(
                row, user=request.user, uploads=uploads(request), **valid(ProofFields, request)
            )
        else:
            raise NotFound()
        record_event(request, f"payment_proof.{operation}", row, row.organization)
        return Response(proof_data(self.mine(row.public_id), tenant=True))


class TenantProofFileView(TenantProofView):
    def get(self, request, public_id):
        portal = portal_context(request)
        item = get_object_or_404(
            PaymentProofFile.objects.filter(
                organization=portal.organization, proof__tenant_id__in=portal.tenant_ids
            ),
            public_id=public_id,
        )
        return evidence_response(item)

