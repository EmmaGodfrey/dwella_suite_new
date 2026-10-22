from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count
from django.http import FileResponse
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from apps.accounts.models import IdentityVerification
from apps.accounts.serializers import IdentityVerificationSerializer
from apps.common.permissions import IsPlatformAdmin

from .services import record_event
from .user_serializers import PlatformUserSerializer


class IdentityReviewSerializer(IdentityVerificationSerializer):
    id = serializers.IntegerField(read_only=True)
    user = PlatformUserSerializer(read_only=True)

    class Meta(IdentityVerificationSerializer.Meta):
        fields = ["id", "user"] + IdentityVerificationSerializer.Meta.fields
        read_only_fields = fields


class IdentityReviewViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsPlatformAdmin]
    serializer_class = IdentityReviewSerializer
    search_fields = ["legal_name", "user__email", "user__first_name", "user__last_name"]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        counts = dict(IdentityVerification.objects.values_list("status").annotate(
            total=Count("pk"),
        ))
        return Response({
            status: counts.get(status, 0) for status in ["pending", "approved", "rejected"]
        })

    def get_queryset(self):
        queryset = IdentityVerification.objects.exclude(status="not_submitted").select_related(
            "user__profile", "user__two_factor_device",
        ).prefetch_related("user__organization_memberships__organization").order_by("submitted_at")
        status = self.request.query_params.get("status")
        if status:
            if status not in IdentityVerification.Status.values:
                raise ValidationError({"status": "Choose a valid identity status."})
            queryset = queryset.filter(status=status)
        class Dates(serializers.Serializer):
            submitted_after = serializers.DateField(required=False)
            submitted_before = serializers.DateField(required=False)
        dates = Dates(data=dict(self.request.query_params.items()))
        dates.is_valid(raise_exception=True)
        values = dates.validated_data
        if values.get("submitted_after") and values.get("submitted_before") and (
            values["submitted_after"] > values["submitted_before"]
        ):
            raise ValidationError("Start date must not be after end date.")
        for name, lookup in [("submitted_after", "gte"), ("submitted_before", "lte")]:
            if name in values:
                queryset = queryset.filter(**{f"submitted_at__date__{lookup}": values[name]})
        return queryset

    def get_throttles(self):
        self.throttle_scope = "platform_write" if self.request.method == "POST" else None
        return super().get_throttles()

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def review(self, request, pk=None):
        class Decision(serializers.Serializer):
            decision = serializers.ChoiceField(choices=["approved", "rejected"])
            reason = serializers.CharField(max_length=300, required=False, allow_blank=True)

        data = Decision(data=request.data)
        data.is_valid(raise_exception=True)
        target = self.get_object()
        verification = IdentityVerification.objects.select_for_update().get(pk=target.pk)
        if verification.status != "pending":
            raise ValidationError("Only pending identity checks can be reviewed.")
        decision, reason = data.validated_data["decision"], data.validated_data.get("reason", "")
        if decision == "rejected" and len(reason) < 5:
            raise ValidationError({"reason": "Explain the rejection in at least 5 characters."})
        verification.status = decision
        verification.rejection_reason = reason if decision == "rejected" else ""
        verification.reviewed_at = timezone.now()
        verification.save(update_fields=["status", "rejection_reason", "reviewed_at", "updated_at"])
        record_event(request, f"identity.{decision}", verification, reason=reason)
        if settings.EMAIL_HOST and "smtp" in settings.EMAIL_BACKEND:
            transaction.on_commit(lambda: send_mail(
                "Your Dwella identity review", f"Your identity check was {decision}. {reason}",
                settings.DEFAULT_FROM_EMAIL, [verification.user.email], fail_silently=False,
            ), robust=True)
        return Response(self.get_serializer(verification).data)

    @action(detail=True, methods=["get"])
    def document(self, request, pk=None):
        verification = self.get_object()
        if not verification.document_image:
            raise NotFound("No identity document is available.")
        record_event(request, "identity.document_viewed", verification)
        try:
            document = verification.document_image.open("rb")
        except FileNotFoundError as exc:
            raise NotFound("No identity document is available.") from exc
        response = FileResponse(
            document, as_attachment=True,
            filename=f"identity-{verification.pk}", content_type="application/octet-stream",
        )
        response["Cache-Control"] = "private, no-store"
        return response
