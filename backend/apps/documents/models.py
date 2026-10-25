from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.common.models import OrganizationScopedModel, TimeStampedModel, UUIDModel


class DocumentVersion(OrganizationScopedModel):
    class Kind(models.TextChoices):
        INVOICE = "invoice", "Invoice"
        LEASE = "lease", "Lease agreement"

    class Status(models.TextChoices):
        READY = "ready", "Ready for review"
        SIGNING = "signing", "Awaiting signatures"
        SIGNED = "signed", "Signed"
        SUPERSEDED = "superseded", "Superseded"
        REVOKED = "revoked", "Signing revoked"

    kind = models.CharField(max_length=12, choices=Kind.choices)
    invoice = models.ForeignKey("billing.Invoice", null=True, on_delete=models.PROTECT)
    lease = models.ForeignKey("leases.Lease", null=True, on_delete=models.PROTECT)
    version = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.READY)
    snapshot = models.JSONField()
    source_fingerprint = models.CharField(max_length=64)
    # The original, kept only once signing replaces `pdf`; empty until then.
    unsigned_pdf = models.BinaryField(editable=False)
    pdf = models.BinaryField(editable=False)
    sha256 = models.CharField(max_length=64)
    page_count = models.PositiveIntegerField()
    copies_emailed_at = models.DateTimeField(null=True)
    delivery_failed = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    landlord_signer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.PROTECT,
        related_name="lease_documents_to_sign",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(kind="invoice", invoice__isnull=False, lease__isnull=True)
                    | Q(kind="lease", lease__isnull=False, invoice__isnull=True)
                ),
                name="document_parent_matches_kind",
            ),
            models.UniqueConstraint(fields=["lease", "version"], name="lease_document_version"),
            models.UniqueConstraint(fields=["invoice", "version"], name="invoice_document_version"),
        ]

    def __str__(self):
        return f"{self.kind} {self.public_id} v{self.version}"


class DocumentSignature(UUIDModel, TimeStampedModel):
    document = models.ForeignKey(
        DocumentVersion, on_delete=models.PROTECT, related_name="signatures"
    )
    role = models.CharField(max_length=12, choices=[("landlord", "Landlord"), ("tenant", "Tenant")])
    signer_name = models.CharField(max_length=180)
    signer_email = models.EmailField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    authentication_method = models.CharField(max_length=20)
    source = models.CharField(max_length=12, choices=[("drawn", "Drawn"), ("uploaded", "Uploaded")])
    png = models.BinaryField(editable=False)
    consent = models.TextField()
    signed_at = models.DateTimeField()
    reviewed_sha256 = models.CharField(max_length=64)
    signed_pdf = models.BinaryField(editable=False)
    sha256 = models.CharField(max_length=64)

    class Meta:
        ordering = ["signed_at"]
        constraints = [
            models.UniqueConstraint(fields=["document", "role"], name="one_signature_per_role"),
        ]

    def __str__(self):
        return f"{self.role}: {self.signer_name}"


class SigningInvite(UUIDModel, TimeStampedModel):
    document = models.ForeignKey(DocumentVersion, on_delete=models.PROTECT, related_name="invites")
    token_hash = models.CharField(max_length=64, unique=True)
    email = models.EmailField()
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)
    consumed_at = models.DateTimeField(null=True)
    otp_hash = models.CharField(max_length=128, blank=True)
    otp_expires_at = models.DateTimeField(null=True)
    otp_requested_at = models.DateTimeField(null=True)
    otp_attempts = models.PositiveSmallIntegerField(default=0)
    session_hash = models.CharField(max_length=64, blank=True)
    session_expires_at = models.DateTimeField(null=True)

    def __str__(self):
        return f"Signing invitation {self.public_id}"


class SignedLeaseOriginal(OrganizationScopedModel):
    lease = models.ForeignKey(
        "leases.Lease", on_delete=models.PROTECT, related_name="signed_originals"
    )
    filename = models.CharField(max_length=180)
    pdf = models.BinaryField(editable=False)
    sha256 = models.CharField(max_length=64)
    page_count = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    note = models.CharField(max_length=500)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.filename


class SigningEmail(UUIDModel, TimeStampedModel):
    """Transactional email intent. Sensitive link/code payloads are encrypted."""

    class Kind(models.TextChoices):
        INVITATION = "invitation", "Invitation"
        OTP = "otp", "Verification code"
        COMPLETED = "completed", "Completed copies"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENDING = "sending", "Sending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    document = models.ForeignKey(DocumentVersion, on_delete=models.PROTECT)
    invite = models.ForeignKey(SigningInvite, null=True, on_delete=models.PROTECT)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    dedupe_key = models.CharField(max_length=180, unique=True)
    encrypted_payload = models.BinaryField(editable=False)
    expires_at = models.DateTimeField()
    next_attempt_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    claim_token = models.UUIDField(null=True, editable=False)
    locked_until = models.DateTimeField(null=True)
    sent_at = models.DateTimeField(null=True)
    failure_code = models.CharField(max_length=40, blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "next_attempt_at"], name="signing_email_due")]
