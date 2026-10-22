from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.organizations.models import Organization, OrganizationMembership
from apps.organizations.services import create_workspace

from .models import SupportSession
from .services import record_event
from .user_services import require_superuser


class WorkspaceProfileInput(serializers.ModelSerializer):
    display_name = serializers.CharField(max_length=180)
    phone_number = serializers.RegexField(r"^\+?[\d\s-]{7,40}$", required=False, allow_blank=True)

    class Meta:
        model = Organization
        fields = ["display_name", "email", "phone_number", "address", "town", "country",
                  "currency", "timezone"]

    def validate_currency(self, value):
        if value != "ZMW":
            raise serializers.ValidationError("Only ZMW is currently supported.")
        return value

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise serializers.ValidationError("Choose a valid timezone.") from exc
        return value


class CreateWorkspaceInput(WorkspaceProfileInput):
    owner = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(is_active=True),
    )

    class Meta(WorkspaceProfileInput.Meta):
        fields = WorkspaceProfileInput.Meta.fields + ["owner"]


def lock_workspace(public_id):
    # Support writes lock their session before touching the workspace. Preserve
    # that order for lifecycle operations; never hold an org lock waiting on one.
    sessions = list(SupportSession.objects.select_for_update(of=("self",)).filter(
        organization__public_id=public_id, ended_at__isnull=True,
    ).order_by("pk"))
    workspace = get_object_or_404(Organization.objects.select_for_update(), public_id=public_id)
    return workspace, sessions


class WorkspaceActions:
    def get_throttles(self):
        self.throttle_scope = "platform_write" if self.request.method == "POST" else None
        return super().get_throttles()

    @transaction.atomic
    def create(self, request):
        data = CreateWorkspaceInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = dict(data.validated_data)
        owner = get_object_or_404(get_user_model().objects.select_for_update(),
                                  pk=values.pop("owner").pk, is_active=True)
        workspace = create_workspace(owner, **values)
        record_event(request, "workspace.created", workspace, organization=workspace,
                     owner_id=owner.pk)
        return Response(self.get_serializer(self.get_queryset().get(pk=workspace.pk)).data,
                        status=201)

    @transaction.atomic
    def partial_update(self, request, public_id=None):
        workspace = get_object_or_404(Organization.objects.select_for_update(),
                                     public_id=public_id)
        data = WorkspaceProfileInput(workspace, data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        data.save()
        record_event(request, "workspace.updated", workspace, organization=workspace,
                     fields=list(data.validated_data))
        return Response(self.get_serializer(self.get_queryset().get(pk=workspace.pk)).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def status(self, request, public_id=None):
        class StatusInput(serializers.Serializer):
            active = serializers.BooleanField()
        data = StatusInput(data=request.data)
        data.is_valid(raise_exception=True)
        if "active" not in request.data:
            raise ValidationError({"active": "This field is required."})
        workspace, sessions = lock_workspace(public_id)
        for session in sessions:
            session.ended_at = timezone.now()
            session.save(update_fields=["ended_at", "updated_at"])
            record_event(request, "support_session.ended", session, organization=workspace,
                         reason="Workspace status changed", support_session=str(session.public_id))
        workspace.is_active = data.validated_data["active"]
        workspace.save(update_fields=["is_active", "updated_at"])
        record_event(request, "workspace.reactivated" if workspace.is_active else
                     "workspace.suspended", workspace, organization=workspace)
        return Response(self.get_serializer(self.get_queryset().get(pk=workspace.pk)).data)

    @action(detail=True, methods=["post"], url_path="transfer-owner")
    @transaction.atomic
    def transfer_owner(self, request, public_id=None):
        class TransferInput(serializers.Serializer):
            owner = serializers.PrimaryKeyRelatedField(
                queryset=get_user_model().objects.filter(is_active=True),
            )
        data = TransferInput(data=request.data)
        data.is_valid(raise_exception=True)
        owner = get_object_or_404(get_user_model().objects.select_for_update(),
                                  pk=data.validated_data["owner"].pk, is_active=True)
        workspace = get_object_or_404(Organization.objects.select_for_update(),
                                     public_id=public_id)
        if not workspace.is_active:
            raise ValidationError("Reactivate the workspace before transferring ownership.")
        OrganizationMembership.objects.filter(
            organization=workspace, role="owner", is_active=True,
        ).exclude(user=owner).update(role="admin", updated_at=timezone.now())
        OrganizationMembership.objects.update_or_create(
            organization=workspace, user=owner, defaults={"role": "owner", "is_active": True},
        )
        record_event(request, "workspace.owner_transferred", workspace, organization=workspace,
                     owner_id=owner.pk)
        return Response(self.get_serializer(self.get_queryset().get(pk=workspace.pk)).data)

    @transaction.atomic
    def destroy(self, request, public_id=None):
        require_superuser(request)
        workspace, _ = lock_workspace(public_id)
        if workspace.is_active:
            raise ValidationError("Suspend the workspace before deleting it.")
        expected = f"DELETE {workspace}"
        if request.data.get("confirmation") != expected:
            raise ValidationError({"confirmation": f"Type {expected} to confirm."})
        record_event(request, "workspace.deleted", workspace, organization=workspace,
                     workspace_name=str(workspace))
        try:
            with transaction.atomic():
                workspace.delete()
        except ProtectedError as exc:
            raise ValidationError(
                "Retained financial or tenancy records prevent deletion.",
            ) from exc
        return Response(status=204)
