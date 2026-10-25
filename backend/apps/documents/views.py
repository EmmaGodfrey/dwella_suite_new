import base64
import io
from uuid import UUID

from django.core.cache import cache
from django.core.files.uploadhandler import FileUploadHandler, StopUpload
from django.db.models import Prefetch
from django.http import FileResponse, HttpResponse
from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.viewsets import OrganizationScopedModelViewSet
from apps.organizations.models import OrganizationMembership

from .files import MAX_SOURCE_BYTES, inspect_pdf, source_preview
from .models import DocumentSignature, DocumentVersion, SignedLeaseOriginal
from .serializers import (
    AttachOriginalSerializer,
    CodeSerializer,
    DocumentSerializer,
    InviteSerializer,
    OriginalSerializer,
    PrepareLeaseSerializer,
    PublicDocumentSerializer,
    SignSerializer,
    SourcePreviewSerializer,
)
from .services import attach_original, create_lease_document
from .signing import (
    add_signature,
    issue_invite,
    request_code,
    revoke_signing,
    send_completed_copies,
    verified_invite,
    verify_code,
)
from .throttles import (
    PAGE_CACHE_SECONDS,
    DocumentRenderThrottle,
    DocumentWriteThrottle,
    SigningIPThrottle,
    SigningLinkThrottle,
    page_cache_key,
)


def private_headers(response):
    response["Cache-Control"] = "private, no-store"
    response["Referrer-Policy"] = "no-referrer"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def pdf_response(raw, filename):
    response = FileResponse(
        io.BytesIO(bytes(raw)),
        content_type="application/pdf",
        as_attachment=True,
        filename=filename,
    )
    response["Content-Security-Policy"] = "sandbox; default-src 'none'"
    return private_headers(response)


def page_response(request, raw, sha256):
    if request.query_params.get("sha256") != sha256:
        raise ValidationError("The document changed. Refresh its preview.")
    try:
        page = int(request.query_params.get("page", "1"))
    except (TypeError, ValueError) as error:
        raise ValidationError({"page": ["Choose a valid page."]}) from error
    if not 1 <= page <= 50:
        raise ValidationError({"page": ["Choose a page from 1 to 50."]})
    # A saved version never changes, so its rendered pages are reusable by digest.
    key = page_cache_key(sha256, page)
    image = cache.get(key)
    if image is None:
        image = base64.b64decode(inspect_pdf(bytes(raw), page=page)["image"])
        cache.set(key, image, PAGE_CACHE_SECONDS)
    return private_headers(HttpResponse(image, content_type="image/png"))


class BoundedUploadHandler(FileUploadHandler):
    def __init__(self, request):
        super().__init__(request)
        self.total = 0
        self.files = 0

    def new_file(self, *args, **kwargs):
        super().new_file(*args, **kwargs)
        self.files += 1
        if self.files > 1:
            raise StopUpload(connection_reset=True)

    def receive_data_chunk(self, raw_data, start):
        self.total += len(raw_data)
        if self.total > MAX_SOURCE_BYTES:
            raise StopUpload(connection_reset=True)
        return raw_data

    def file_complete(self, file_size):
        return None


class PrivateDocumentMixin:
    def initial(self, request, *args, **kwargs):
        request._request.upload_handlers.insert(0, BoundedUploadHandler(request._request))
        super().initial(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        return private_headers(super().finalize_response(request, response, *args, **kwargs))


class DocumentFilter(filters.FilterSet):
    lease = filters.UUIDFilter(field_name="lease__public_id")
    invoice = filters.UUIDFilter(field_name="invoice__public_id")

    class Meta:
        model = DocumentVersion
        fields = ["kind", "lease", "invoice"]


class DocumentViewSet(PrivateDocumentMixin, OrganizationScopedModelViewSet):
    serializer_class = DocumentSerializer
    queryset = (
        DocumentVersion.objects.select_related(
            "organization",
            "lease__organization",
            "lease__tenant",
            "lease__unit__property",
            "landlord_signer",
        )
        .defer("pdf", "unsigned_pdf")
        .prefetch_related(
            Prefetch("signatures", queryset=DocumentSignature.objects.defer("png", "signed_pdf"))
        )
    )
    http_method_names = ["get", "post", "head", "options"]
    filterset_class = DocumentFilter

    def get_throttles(self):
        result = super().get_throttles()
        if self.request.method == "POST":
            result.append(DocumentWriteThrottle())
        if self.action == "page":
            result.append(DocumentRenderThrottle())
        return result

    def create(self, request, *args, **kwargs):
        serializer = PrepareLeaseSerializer(
            data=request.data,
            context={
                "request": request,
                "organization": self.get_organization(),
            },
        )
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        lease = data.pop("lease")
        document = create_lease_document(request, lease, data)
        return Response(self.get_serializer(document).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def signers(self, request):
        members = OrganizationMembership.objects.filter(
            organization=self.get_organization(),
            is_active=True,
            role="landlord",
            user__is_active=True,
            user__is_staff=False,
            user__is_superuser=False,
        ).select_related("user")
        return Response(
            [
                {
                    "id": m.user_id,
                    "name": m.user.get_full_name() or m.user.email,
                    "email": m.user.email,
                }
                for m in members
                if m.user.email
            ]
        )

    @action(detail=True, methods=["get"])
    def pdf(self, request, public_id=None):
        doc = self.get_object()
        return pdf_response(doc.pdf, f"{doc.snapshot['reference']}-v{doc.version}.pdf")

    @action(detail=True, methods=["get"])
    def page(self, request, public_id=None):
        doc = self.get_object()
        return page_response(request, doc.pdf, doc.sha256)

    @action(detail=True, methods=["get"], url_path=r"signatures/(?P<signature_id>[^/.]+)/pdf")
    def signature_pdf(self, request, public_id=None, signature_id=None):
        try:
            signature_uuid = UUID(signature_id)
        except (ValueError, TypeError) as error:
            raise NotFound() from error
        signature = self.get_object().signatures.filter(public_id=signature_uuid).first()
        if not signature:
            raise NotFound()
        return pdf_response(signature.signed_pdf, "signed-revision.pdf")

    @action(detail=True, methods=["post"])
    def invite(self, request, public_id=None):
        data = InviteSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(issue_invite(request, self.get_object(), **data.validated_data))

    @action(detail=True, methods=["post"])
    def sign(self, request, public_id=None):
        data = SignSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        document = add_signature(request, self.get_object(), data.validated_data)
        return Response(self.get_serializer(document).data)

    @action(detail=False, methods=["post"], url_path="source-preview")
    def source(self, request):
        data = SourcePreviewSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(source_preview(**data.validated_data))

    @action(detail=True, methods=["post"])
    def revoke(self, request, public_id=None):
        document = revoke_signing(request, self.get_object())
        return Response(self.get_serializer(document).data)

    @action(detail=True, methods=["post"], url_path="email-copies")
    def email_copies(self, request, public_id=None):
        document = self.get_object()
        if document.status != "signed":
            raise ValidationError("Copies can be emailed after all parties have signed.")
        delivered = send_completed_copies(document.pk)
        return Response({"delivered": delivered})


class OriginalViewSet(PrivateDocumentMixin, OrganizationScopedModelViewSet):
    serializer_class = OriginalSerializer
    queryset = SignedLeaseOriginal.objects.select_related("lease", "organization").defer("pdf")
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        lease = self.request.query_params.get("lease")
        if lease:
            try:
                return queryset.filter(lease__public_id=UUID(lease))
            except ValueError as error:
                raise ValidationError({"lease": ["Choose a valid lease."]}) from error
        return queryset

    def get_throttles(self):
        return [*super().get_throttles(), DocumentWriteThrottle()]

    def create(self, request, *args, **kwargs):
        data = AttachOriginalSerializer(
            data=request.data,
            context={
                "organization": self.get_organization(),
            },
        )
        data.is_valid(raise_exception=True)
        attachment = attach_original(
            request,
            data.validated_data["lease"],
            data.validated_data["file"],
            data.validated_data["note"],
        )
        return Response(self.get_serializer(attachment).data, status=201)

    @action(detail=True, methods=["get"])
    def pdf(self, request, public_id=None):
        attachment = self.get_object()
        return pdf_response(attachment.pdf, attachment.filename)


class PublicSigningView(PrivateDocumentMixin, APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [SigningIPThrottle, SigningLinkThrottle]

    def get(self, request, token, operation):
        invite = verified_invite(request, token, read=True)
        document = invite.document
        if operation == "document":
            return Response(PublicDocumentSerializer(document, context={"request": request}).data)
        if operation == "pdf":
            return pdf_response(document.pdf, f"{document.snapshot['reference']}.pdf")
        if operation == "page":
            return page_response(request, document.pdf, document.sha256)
        raise NotFound()

    def post(self, request, token, operation):
        if operation == "request-code":
            request_code(request, token)
            return Response(
                {
                    "message": "If this invitation is available, "
                    "a code has been sent to its recipient."
                }
            )
        if operation == "verify":
            data = CodeSerializer(data=request.data)
            data.is_valid(raise_exception=True)
            return Response(verify_code(request, token, data.validated_data["code"]))
        invite = verified_invite(request, token)
        if operation == "source-preview":
            data = SourcePreviewSerializer(data=request.data)
            data.is_valid(raise_exception=True)
            return Response(source_preview(**data.validated_data))
        if operation == "sign":
            data = SignSerializer(data=request.data)
            data.is_valid(raise_exception=True)
            document = add_signature(
                request, invite.document, {**data.validated_data, "token": token}, invite=invite
            )
            return Response(PublicDocumentSerializer(document, context={"request": request}).data)
        raise NotFound()
