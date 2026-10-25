from decimal import Decimal

from django.db import transaction
from django.db.models import F, Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.billing.models import Invoice, Payment
from apps.documents.models import DocumentSignature, DocumentVersion, SignedLeaseOriginal
from apps.documents.services import create_invoice_document
from apps.documents.throttles import DocumentRenderThrottle
from apps.documents.views import page_response, pdf_response, private_headers
from apps.leases.models import Lease
from apps.maintenance.models import MaintenanceRequest, MaintenanceUpdate
from apps.maintenance.serializers import MAX_PHOTOS
from apps.maintenance.serializers import MaintenancePhotoSerializer as PhotoUploadSerializer
from apps.maintenance.services import create_request

from .access import IsPortalTenant, portal_context
from .serializers import (
    DocumentSerializer,
    InvoiceDetailSerializer,
    InvoiceSerializer,
    LeaseSerializer,
    MaintenanceDetailSerializer,
    MaintenanceSerializer,
    MaintenanceUpdateSerializer,
    OriginalSerializer,
    PaymentSerializer,
    ProfileSerializer,
    ReceiptSerializer,
    issuer,
)

# Draft leases are the manager's working copy until they are sent for signing.
VISIBLE_LEASE_STATUSES = (
    Lease.Status.PENDING_SIGNATURE,
    Lease.Status.ACTIVE,
    Lease.Status.ENDED,
)
# A version being prepared, replaced or withdrawn is not the tenant's agreement.
VISIBLE_DOCUMENT_STATUSES = (DocumentVersion.Status.SIGNING, DocumentVersion.Status.SIGNED)


class PortalWriteThrottle(UserRateThrottle):
    scope = "portal_write"
    rate = "60/hour"


class PortalMixin:
    permission_classes = [IsPortalTenant]
    lookup_field = "public_id"
    lookup_url_kwarg = "public_id"

    @property
    def portal(self):
        return portal_context(self.request)


def leases(portal):
    return portal.scope(Lease.objects.filter(is_active=True, status__in=VISIBLE_LEASE_STATUSES))


def invoices(portal):
    return portal.scope(Invoice.objects.filter(is_active=True))


def payments(portal):
    return portal.scope(Payment.objects.all())


def requests(portal):
    return portal.scope(MaintenanceRequest.objects.filter(is_active=True))


def documents(portal):
    return (
        DocumentVersion.objects.filter(
            organization=portal.organization,
            kind=DocumentVersion.Kind.LEASE,
            lease__in=leases(portal),
            status__in=VISIBLE_DOCUMENT_STATUSES,
        )
        .select_related("lease")
        .defer("pdf", "unsigned_pdf")
        .prefetch_related(
            Prefetch(
                "signatures",
                queryset=DocumentSignature.objects.defer("png", "signed_pdf").order_by("signed_at"),
            )
        )
    )


class OverviewView(PortalMixin, APIView):
    def get(self, request):
        portal = self.portal
        unpaid = invoices(portal).filter(status__in=Invoice.UNPAID_STATUSES)
        owed = F("total") - F("amount_paid")
        totals = unpaid.aggregate(
            balance=Coalesce(Sum(owed), Decimal("0")),
            overdue=Coalesce(Sum(owed, filter=Q(due_date__lt=timezone.localdate())), Decimal("0")),
        )
        next_due = (
            unpaid.select_related("lease", "unit__property")
            .prefetch_related("lines")
            .order_by("due_date", "created_at")
            .first()
        )
        current = (
            leases(portal)
            .filter(status__in=(Lease.Status.PENDING_SIGNATURE, Lease.Status.ACTIVE))
            .select_related("unit__property")
        )
        tenant = portal.tenants[0]
        return Response(
            {
                "tenant": {"name": tenant.full_name, "status": tenant.status},
                "manager": issuer(portal.organization),
                # Strings, like every other money field the API returns.
                "balance": f"{totals['balance']:.2f}",
                "overdue_balance": f"{totals['overdue']:.2f}",
                "next_due": InvoiceSerializer(next_due).data if next_due else None,
                "current_leases": LeaseSerializer(current, many=True).data,
                "awaiting_signature": [
                    doc
                    for doc in DocumentSerializer(
                        documents(portal).filter(status=DocumentVersion.Status.SIGNING),
                        many=True,
                    ).data
                    if doc["awaiting_your_signature"]
                ],
                "open_repairs": requests(portal)
                .filter(status__in=MaintenanceRequest.OPEN_STATUSES)
                .count(),
                "recent_payments": PaymentSerializer(
                    payments(portal)
                    .filter(reversed_at__isnull=True)
                    .select_related("invoice")
                    .order_by("-paid_on", "-created_at")[:3],
                    many=True,
                ).data,
            }
        )


class LeaseListView(PortalMixin, generics.ListAPIView):
    serializer_class = LeaseSerializer

    def get_queryset(self):
        return leases(self.portal).select_related("unit__property").order_by("-start_date")


class LeaseDetailView(PortalMixin, generics.RetrieveAPIView):
    serializer_class = LeaseSerializer

    def get_queryset(self):
        return leases(self.portal).select_related("unit__property")


class LeaseDocumentsView(PortalMixin, APIView):
    def get(self, request, public_id):
        lease = generics.get_object_or_404(leases(self.portal), public_id=public_id)
        versions = documents(self.portal).filter(lease=lease).select_related("lease")
        originals = (
            SignedLeaseOriginal.objects.filter(organization=self.portal.organization, lease=lease)
            .select_related("lease")
            .defer("pdf")
        )
        return private_headers(
            Response(
                {
                    "versions": DocumentSerializer(versions.order_by("-version"), many=True).data,
                    "originals": OriginalSerializer(
                        originals.order_by("-created_at"), many=True
                    ).data,
                }
            )
        )


class DocumentFileView(PortalMixin, APIView):
    throttle_classes = [DocumentRenderThrottle]

    def get(self, request, public_id, operation):
        if operation not in {"pdf", "page"}:
            raise NotFound()
        document = generics.get_object_or_404(
            documents(self.portal).defer(None).defer("unsigned_pdf").prefetch_related(None),
            public_id=public_id,
        )
        if operation == "page":
            return page_response(request, document.pdf, document.sha256)
        filename = f"{document.snapshot['reference']}-v{document.version}.pdf"
        return pdf_response(document.pdf, filename)


class OriginalFileView(PortalMixin, APIView):
    throttle_classes = [DocumentRenderThrottle]

    def get(self, request, public_id):
        original = generics.get_object_or_404(
            SignedLeaseOriginal.objects.filter(
                organization=self.portal.organization, lease__in=leases(self.portal)
            ),
            public_id=public_id,
        )
        return pdf_response(original.pdf, original.filename)


class InvoiceListView(PortalMixin, generics.ListAPIView):
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        queryset = invoices(self.portal).select_related("lease", "unit__property")
        if self.request.query_params.get("unpaid") == "true":
            queryset = queryset.filter(status__in=Invoice.UNPAID_STATUSES)
        return queryset.prefetch_related("lines").order_by("-due_date", "-created_at")


class InvoiceDetailView(PortalMixin, generics.RetrieveAPIView):
    serializer_class = InvoiceDetailSerializer

    def get_queryset(self):
        return (
            invoices(self.portal)
            .select_related("organization", "lease", "unit__property")
            .prefetch_related(
                "lines",
                Prefetch(
                    "payments",
                    queryset=Payment.objects.select_related("invoice").order_by("paid_on"),
                ),
            )
        )


class InvoiceFileView(PortalMixin, APIView):
    throttle_classes = [DocumentRenderThrottle]

    def get(self, request, public_id, operation):
        if operation not in {"pdf", "page", "info"}:
            raise NotFound()
        invoice = generics.get_object_or_404(
            invoices(self.portal).exclude(status=Invoice.Status.VOID), public_id=public_id
        )
        # Reuses the saved version unless the invoice changed since it was rendered.
        document = create_invoice_document(request, invoice)
        if operation == "page":
            return page_response(request, document.pdf, document.sha256)
        if operation == "info":
            return private_headers(
                Response(
                    {
                        "id": str(document.public_id),
                        "sha256": document.sha256,
                        "page_count": document.page_count,
                        "version": document.version,
                    }
                )
            )
        return pdf_response(document.pdf, f"{document.snapshot['reference']}.pdf")


class PaymentListView(PortalMixin, generics.ListAPIView):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return payments(self.portal).select_related("invoice").order_by("-paid_on", "-created_at")


class ReceiptView(PortalMixin, generics.RetrieveAPIView):
    serializer_class = ReceiptSerializer

    def get_queryset(self):
        return payments(self.portal).select_related(
            "organization", "tenant", "invoice__unit__property"
        )


class MaintenanceListView(PortalMixin, generics.ListCreateAPIView):
    serializer_class = MaintenanceSerializer

    def get_throttles(self):
        return [PortalWriteThrottle()] if self.request.method == "POST" else super().get_throttles()

    def get_queryset(self):
        queryset = requests(self.portal).select_related("property", "unit", "vendor", "invoice")
        if self.request.query_params.get("open") == "true":
            queryset = queryset.filter(status__in=MaintenanceRequest.OPEN_STATUSES)
        return queryset.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        lease_id = data.pop("lease", None)
        current = (
            leases(self.portal)
            .filter(status__in=(Lease.Status.PENDING_SIGNATURE, Lease.Status.ACTIVE))
            .select_related("unit__property", "tenant")
        )
        if lease_id:
            current = current.filter(public_id=lease_id)
        current = list(current[:2])
        if not current:
            raise ValidationError({"lease": ["Repairs can be reported for a current tenancy."]})
        if len(current) > 1:
            raise ValidationError({"lease": ["Choose which home this repair is for."]})
        lease = current[0]
        job = create_request(
            organization=self.portal.organization,
            reported_by=request.user,
            property=lease.unit.property,
            unit=lease.unit,
            tenant=lease.tenant,
            source=MaintenanceRequest.Source.TENANT,
            **data,
        )
        record_event(request, "maintenance.tenant_reported", job, self.portal.organization)
        return Response(
            MaintenanceSerializer(job, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


class MaintenanceDetailView(PortalMixin, generics.RetrieveAPIView):
    serializer_class = MaintenanceDetailSerializer

    def get_queryset(self):
        return (
            requests(self.portal)
            .select_related("property", "unit", "vendor", "invoice")
            .prefetch_related(
                Prefetch("updates", queryset=MaintenanceUpdate.objects.select_related("author")),
                "photos",
            )
        )


class MaintenanceActionView(PortalMixin, APIView):
    """A tenant adds a message or a photo while the repair is still open."""

    parser_classes = [JSONParser, MultiPartParser, FormParser]
    throttle_classes = [PortalWriteThrottle]

    def post(self, request, public_id, operation):
        if operation not in {"updates", "photos"}:
            raise NotFound()
        with transaction.atomic():
            job = generics.get_object_or_404(
                requests(self.portal).select_for_update(), public_id=public_id
            )
            if job.status not in MaintenanceRequest.OPEN_STATUSES:
                raise ValidationError("This request is closed. Report a new repair instead.")
            if operation == "updates":
                serializer = MaintenanceUpdateSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(
                    request=job,
                    author=request.user,
                    kind=MaintenanceUpdate.Kind.COMMENT,
                    is_internal=False,
                )
            else:
                if job.photos.count() >= MAX_PHOTOS:
                    raise ValidationError(
                        {"image": [f"A request can have up to {MAX_PHOTOS} photos."]}
                    )
                serializer = PhotoUploadSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(request=job, uploaded_by=request.user)
        detail = MaintenanceDetailView.get_queryset(self).get(pk=job.pk)
        return Response(
            MaintenanceDetailSerializer(detail, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ProfileView(PortalMixin, APIView):
    def get_throttles(self):
        if self.request.method == "PATCH":
            return [PortalWriteThrottle()]
        return super().get_throttles()

    def get(self, request):
        return Response(ProfileSerializer(self.portal.tenants[0]).data)

    def patch(self, request):
        if len(self.portal.tenants) != 1:
            raise ValidationError("Ask your property manager to update your contact details.")
        with transaction.atomic():
            tenant = (
                type(self.portal.tenants[0])
                .objects.select_for_update()
                .get(pk=self.portal.tenants[0].pk)
            )
            serializer = ProfileSerializer(tenant, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            previous = tenant.phone_number
            serializer.save()
            if previous != tenant.phone_number:
                record_event(
                    request, "tenant.contact_updated_by_tenant", tenant, tenant.organization
                )
        return Response(serializer.data)
