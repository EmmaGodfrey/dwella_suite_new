from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.services import record_event
from apps.billing.models import Invoice
from apps.leases.models import Lease
from apps.organizations.models import OrganizationMembership

from .models import DocumentVersion, SignedLeaseOriginal
from .rendering import digest, invoice_pdf, lease_pdf
from .snapshots import fingerprint, invoice_source, lease_source


def active_signer(user, organization):
    return bool(
        user
        and user.is_active
        and not user.is_staff
        and not user.is_superuser
        and OrganizationMembership.objects.filter(
            user=user,
            organization=organization,
            is_active=True,
            role="landlord",
        ).exists()
    )


def require_current(document):
    if document.kind != "lease" or document.status not in {"ready", "signing"}:
        raise ValidationError("This document is not open for signing.")
    lease = Lease.objects.select_related("organization", "tenant", "unit__property").get(
        pk=document.lease_id,
    )
    signer = document.landlord_signer
    signer_name = (
        (signer.get_full_name().strip() or signer.email or signer.username) if signer else ""
    )
    if (
        not lease.is_active
        or lease.status == "ended"
        or not lease.tenant.is_active
        or not lease.organization.is_active
        or document.source_fingerprint != fingerprint(lease_source(lease))
        or not active_signer(document.landlord_signer, lease.organization)
        or signer.email.casefold() != document.snapshot["landlord_signer_email"].casefold()
        or signer_name != document.snapshot["landlord_signer_name"]
    ):
        raise ValidationError("The lease or signatory has changed. Create a new document version.")
    return lease


def validate_pdf_size(raw, pages):
    if len(raw) > 8 * 1024**2 or not 1 <= pages <= 50:
        raise ValidationError("Use a document of at most 50 pages and 8 MB.")


@transaction.atomic
def create_invoice_document(request, invoice):
    invoice = (
        Invoice.objects.select_for_update(of=("self",))
        .select_related(
            "organization",
            "tenant",
            "unit__property",
            "lease",
        )
        .get(pk=invoice.pk)
    )
    snapshot = invoice_source(invoice)
    source_hash = fingerprint(snapshot)
    previous = DocumentVersion.objects.filter(invoice=invoice).order_by("-version").first()
    if previous and previous.source_fingerprint == source_hash:
        return previous
    version = (previous.version if previous else 0) + 1
    snapshot["version"] = version
    raw, pages = invoice_pdf(snapshot)
    validate_pdf_size(raw, pages)
    document = DocumentVersion.objects.create(
        organization=invoice.organization,
        invoice=invoice,
        kind="invoice",
        version=version,
        snapshot=snapshot,
        source_fingerprint=source_hash,
        unsigned_pdf=raw,
        pdf=raw,
        sha256=digest(raw),
        page_count=pages,
        created_by=request.user,
    )
    record_event(request, "document.invoice_generated", document, invoice.organization)
    return document


@transaction.atomic
def create_lease_document(request, lease, data):
    lease = (
        Lease.objects.select_for_update(of=("self",))
        .select_related(
            "organization",
            "tenant",
            "unit__property",
        )
        .get(pk=lease.pk)
    )
    if lease.status == "ended" or not lease.is_active or not lease.tenant.is_active:
        raise ValidationError("Use a current lease and tenant before preparing a signing version.")
    signer = data["landlord_signer"]
    if not active_signer(signer, lease.organization):
        raise ValidationError({"landlord_signer": ["Choose an active property-manager account."]})
    if not lease.tenant.email:
        raise ValidationError(
            {"lease": ["Add the tenant's email before preparing a signing document."]}
        )
    source = lease_source(lease)
    version = (
        DocumentVersion.objects.filter(lease=lease).aggregate(n=Max("version"))["n"] or 0
    ) + 1
    snapshot = {
        **source,
        "version": version,
        "prepared_on": timezone.localdate().isoformat(),
        "landlord_name": data["landlord_name"],
        "landlord_address": data["landlord_address"],
        "landlord_signer_name": signer.get_full_name().strip() or signer.email or signer.username,
        "landlord_signer_email": signer.email,
        "agreement_text": data["agreement_text"],
        "schedule_text": data.get("schedule_text", ""),
    }
    raw, pages = lease_pdf(snapshot)
    validate_pdf_size(raw, pages)
    old = list(
        DocumentVersion.objects.select_for_update()
        .filter(
            lease=lease,
            status__in=["ready", "signing"],
        )
        .order_by("pk")
    )
    for item in old:
        item.invites.filter(revoked_at__isnull=True).update(
            revoked_at=timezone.now(), session_hash=""
        )
        item.status = "superseded"
        item.save(update_fields=["status", "updated_at"])
    document = DocumentVersion.objects.create(
        organization=lease.organization,
        lease=lease,
        kind="lease",
        version=version,
        snapshot=snapshot,
        source_fingerprint=fingerprint(source),
        unsigned_pdf=raw,
        pdf=raw,
        sha256=digest(raw),
        page_count=pages,
        created_by=request.user,
        landlord_signer=signer,
    )
    record_event(request, "document.lease_prepared", document, lease.organization, version=version)
    return document


def attach_original(request, lease, upload, note):
    from .files import inspect_pdf, read_upload

    raw = read_upload(upload)
    info = inspect_pdf(raw, render=False)
    with transaction.atomic():
        attachment = SignedLeaseOriginal.objects.create(
            organization=lease.organization,
            lease=lease,
            filename="signed-lease.pdf",
            pdf=raw,
            sha256=digest(raw),
            page_count=info["pages"],
            uploaded_by=request.user,
            note=note,
        )
        record_event(
            request,
            "document.signed_original_uploaded",
            attachment,
            lease.organization,
            sha256=attachment.sha256,
        )
    return attachment
