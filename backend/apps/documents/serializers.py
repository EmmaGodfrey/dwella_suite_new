from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.common.serializers import OrganizationScopedSerializer
from apps.leases.models import Lease

from .models import DocumentSignature, DocumentVersion, SignedLeaseOriginal
from .services import active_signer
from .snapshots import fingerprint, lease_source


class SignatureSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)

    class Meta:
        model = DocumentSignature
        fields = [
            "id",
            "role",
            "signer_name",
            "authentication_method",
            "source",
            "signed_at",
            "consent",
            "reviewed_sha256",
            "sha256",
        ]
        read_only_fields = fields


class DocumentSerializer(OrganizationScopedSerializer):
    signatures = SignatureSerializer(many=True, read_only=True)
    current_terms = serializers.SerializerMethodField()
    landlord_signer_id = serializers.IntegerField(read_only=True)
    can_sign = serializers.SerializerMethodField()

    class Meta:
        model = DocumentVersion
        fields = [
            "id",
            "kind",
            "version",
            "status",
            "snapshot",
            "sha256",
            "page_count",
            "created_at",
            "current_terms",
            "signatures",
            "landlord_signer_id",
            "can_sign",
            "copies_emailed_at",
            "delivery_failed",
        ]
        read_only_fields = fields

    def get_current_terms(self, obj):
        return obj.kind == "invoice" or obj.source_fingerprint == fingerprint(
            lease_source(obj.lease)
        )

    def get_can_sign(self, obj):
        request = self.context.get("request")
        return bool(
            obj.kind == "lease"
            and obj.status in {"ready", "signing"}
            and obj.lease.status != "ended"
            and obj.lease.is_active
            and obj.lease.tenant.is_active
            and self.get_current_terms(obj)
            and request
            and request.user.is_authenticated
            and request.user.pk == obj.landlord_signer_id
            and active_signer(request.user, obj.organization)
            and not obj.signatures.filter(role="landlord").exists()
        )


class PublicDocumentSerializer(DocumentSerializer):
    class Meta(DocumentSerializer.Meta):
        fields = [
            f
            for f in DocumentSerializer.Meta.fields
            if f not in {"landlord_signer_id", "can_sign", "delivery_failed", "copies_emailed_at"}
        ]


class PrepareLeaseSerializer(serializers.Serializer):
    lease = serializers.SlugRelatedField(slug_field="public_id", queryset=Lease.objects.none())
    landlord_name = serializers.CharField(max_length=180)
    landlord_address = serializers.CharField(max_length=2000)
    landlord_signer = serializers.IntegerField(required=False)
    agreement_text = serializers.CharField(min_length=200, max_length=30000)
    schedule_text = serializers.CharField(max_length=10000, required=False, allow_blank=True)
    terms_approved = serializers.BooleanField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        organization = self.context["organization"]
        self.fields["lease"].queryset = Lease.objects.for_organization(organization)

    def validate_terms_approved(self, value):
        if not value:
            raise serializers.ValidationError("Confirm the complete agreement wording is approved.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        signer_id = attrs.get("landlord_signer", request.user.pk)
        signer = get_user_model().objects.filter(pk=signer_id).first()
        if not active_signer(signer, self.context["organization"]) or not signer.email:
            raise serializers.ValidationError(
                {
                    "landlord_signer": [
                        "Choose an active property manager with a permanent email."
                    ],
                }
            )
        attrs["landlord_signer"] = signer
        return attrs


class SignSerializer(serializers.Serializer):
    expected_sha256 = serializers.RegexField(r"^[a-f0-9]{64}$")
    signer_name = serializers.CharField(max_length=180)
    consent = serializers.BooleanField()
    signature = serializers.FileField(max_length=180)
    source = serializers.ChoiceField(choices=["drawn", "uploaded"])

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError("Confirm your intent to sign this agreement.")
        return value


class InviteSerializer(serializers.Serializer):
    email_link = serializers.BooleanField(default=False)


class CodeSerializer(serializers.Serializer):
    code = serializers.RegexField(r"^\d{6}$")


class SourcePreviewSerializer(serializers.Serializer):
    file = serializers.FileField()
    page = serializers.IntegerField(min_value=1, max_value=50, default=1)


class OriginalSerializer(OrganizationScopedSerializer):
    lease = serializers.UUIDField(source="lease.public_id", read_only=True)

    class Meta:
        model = SignedLeaseOriginal
        fields = ["id", "lease", "filename", "sha256", "page_count", "note", "created_at"]
        read_only_fields = fields


class AttachOriginalSerializer(serializers.Serializer):
    lease = serializers.SlugRelatedField(slug_field="public_id", queryset=Lease.objects.none())
    file = serializers.FileField()
    note = serializers.CharField(min_length=5, max_length=500)
    confirmed_original = serializers.BooleanField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lease"].queryset = Lease.objects.for_organization(self.context["organization"])

    def validate_confirmed_original(self, value):
        if not value:
            raise serializers.ValidationError("Confirm that this is the signed original file.")
        return value
