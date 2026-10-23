from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import SupportSession
from .services import record_event
from .user_serializers import MembershipInput
from .user_services import change_membership, lock_target, protect_account, require_superuser


def revoke_access(request, user):
    user.auth_token.delete() if hasattr(user, "auth_token") else None
    for session in SupportSession.objects.select_for_update().filter(
        admin=user, ended_at__isnull=True,
    ):
        session.ended_at = timezone.now()
        session.save(update_fields=["ended_at", "updated_at"])
        record_event(request, "support_session.ended", session, session.organization,
                     support_session=str(session.public_id), reason=session.reason,
                     cause="account_access_revoked")


class UserAccountActions:
    @action(detail=True, methods=["post"], url_path="status")
    @transaction.atomic
    def account_status(self, request, pk=None):
        target = self.get_object()
        from rest_framework import serializers

        class StatusInput(serializers.Serializer):
            active = serializers.BooleanField()

        if "active" not in request.data:
            raise ValidationError({"active": "This field is required."})
        data = StatusInput(data=request.data)
        data.is_valid(raise_exception=True)
        user = lock_target(request, target.pk)
        active = data.validated_data["active"]
        if not active:
            protect_account(request, user, remove_access=True)
            revoke_access(request, user)
        user.is_active = active
        user.save(update_fields=["is_active"])
        record_event(request, "user.reactivated" if active else "user.deactivated", user)
        return Response(self.get_serializer(user).data)

    @action(detail=True, methods=["post"], url_path="admin-access")
    @transaction.atomic
    def admin_access(self, request, pk=None):
        require_superuser(request)
        target = self.get_object()
        from rest_framework import serializers

        class AdminInput(serializers.Serializer):
            enabled = serializers.BooleanField()

        if "enabled" not in request.data:
            raise ValidationError({"enabled": "This field is required."})
        data = AdminInput(data=request.data)
        data.is_valid(raise_exception=True)
        user = lock_target(request, target.pk)
        enabled = data.validated_data["enabled"]
        if not enabled:
            protect_account(request, user)
            revoke_access(request, user)
        # Dwella has one platform tier: a super admin is always staff and superuser.
        user.is_staff = user.is_superuser = enabled
        user.save(update_fields=["is_staff", "is_superuser"])
        record_event(request, "user.admin_granted" if enabled else "user.admin_revoked", user)
        return Response(self.get_serializer(user).data)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        require_superuser(request)
        user = lock_target(request, self.get_object().pk)
        protect_account(request, user, remove_access=True)
        expected = f"DELETE {user.get_full_name() or user.email or user.username}"
        if user.is_active or request.data.get("confirmation") != expected:
            raise ValidationError({
                "confirmation": "Deactivate the user first, then type the required confirmation.",
            })
        record_event(request, "user.deleted", user)
        user.delete()
        return Response(status=204)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def membership(self, request, pk=None):
        user = self.get_object()
        serializer = MembershipInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = change_membership(request, user, **serializer.validated_data)
        record_event(request, "user.membership_changed", membership, membership.organization,
                     user_id=user.pk, role=membership.role, active=membership.is_active)
        return Response(self.get_serializer(self.get_queryset().get(pk=user.pk)).data)
