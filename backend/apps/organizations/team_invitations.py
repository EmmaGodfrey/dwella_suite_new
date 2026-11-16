"""Accepting an emailed invitation to manage a workspace."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.access_state import mark_email_verified
from apps.accounts.email_verification import (
    NoStoreAccountView,
    VerificationTokenSerializer,
    secret_hash,
)
from apps.accounts.throttles import InvitationIPThrottle, InvitationTokenThrottle
from apps.audit.services import record_event

from .models import Organization, OrganizationMembership, PropertyAssignment, TeamInvitation

INVALID = "This invitation has expired or is unavailable. Ask a property admin for a new one."
Role = OrganizationMembership.Role


def find_invitation(token):
    invitation = (
        TeamInvitation.objects.select_related("organization")
        .filter(token_hash=secret_hash(token))
        .first()
    )
    if (
        not invitation
        or invitation.revoked_at
        or invitation.accepted_at
        or invitation.expires_at <= timezone.now()
        or not invitation.organization.is_active
        or invitation.role not in OrganizationMembership.MANAGEMENT_ROLES
    ):
        raise ValidationError(INVALID)
    return invitation


@transaction.atomic
def accept_team_invitation(request, token, password="", full_name=""):
    candidate = find_invitation(token)
    # The same lock team changes take, so two acceptances cannot interleave.
    Organization.objects.select_for_update().get(pk=candidate.organization_id)
    invitation = TeamInvitation.objects.select_for_update().get(pk=candidate.pk)
    find_invitation(token)  # Recheck after the locks.
    organization = invitation.organization
    users = get_user_model().objects.select_for_update().filter(email__iexact=invitation.email)
    if users.count() > 1:
        raise ValidationError(INVALID)
    user = users.first()
    if user:
        if not request.user.is_authenticated or request.user.pk != user.pk:
            raise PermissionDenied(
                {
                    "message": "Sign in with the invited email to accept.",
                    "code": "invitation_sign_in_required",
                }
            )
    else:
        if request.user.is_authenticated:
            raise PermissionDenied(
                "Sign out of the other account before accepting this invitation."
            )
        name = " ".join((full_name or invitation.full_name).split())
        if len(name) < 2:
            raise ValidationError({"full_name": ["Enter your full name."]})
        if not password:
            raise ValidationError({"password": ["Choose a password for your new account."]})
        first, _, last = name.partition(" ")
        user = get_user_model()(
            username=invitation.email,
            email=invitation.email,
            first_name=first[:150],
            last_name=last[:150],
        )
        try:
            validate_password(password, user=user)
        except DjangoValidationError as error:
            raise ValidationError({"password": error.messages}) from error
        user.set_password(password)
        try:
            with transaction.atomic():
                user.save()
        except IntegrityError as error:
            raise ValidationError("Sign in with the invited email, then accept again.") from error
    # One account holds one role in one workspace: an account that is already a
    # tenant or works in another workspace cannot be turned into a manager here.
    if (
        not user.is_active
        or user.is_staff
        or user.is_superuser
        or OrganizationMembership.objects.filter(user=user, is_active=True).exists()
    ):
        raise PermissionDenied("This account cannot join this team. Contact support.")
    membership, created = OrganizationMembership.objects.get_or_create(
        user=user,
        organization=organization,
        defaults={"role": invitation.role, "invited_by": invitation.created_by},
    )
    if not created:
        if membership.role == Role.TENANT:
            raise PermissionDenied("This account cannot join this team. Contact support.")
        # Someone removed earlier and invited back: start again from this invitation.
        membership.property_assignments.all().delete()
        membership.role, membership.is_active = invitation.role, True
        membership.invited_by = invitation.created_by
        membership.save(update_fields=["role", "is_active", "invited_by", "updated_at"])
    if invitation.role == Role.MANAGER:
        PropertyAssignment.objects.bulk_create(
            PropertyAssignment(
                organization=organization,
                membership=membership,
                property=item,
                assigned_by=invitation.created_by,
            )
            for item in invitation.properties.filter(organization=organization)
        )
    invitation.accepted_at, invitation.accepted_by = timezone.now(), user
    invitation.save(update_fields=["accepted_at", "accepted_by", "updated_at"])
    mark_email_verified(user)
    record_event(
        request,
        "team.invitation_accepted",
        invitation,
        organization,
        member=user.pk,
        member_name=user.get_full_name().strip() or user.email,
        role=invitation.role,
    )
    return {"accepted": True, "sign_in_required": not request.user.is_authenticated}


class TeamInvitationAcceptSerializer(VerificationTokenSerializer):
    password = serializers.CharField(
        max_length=128, required=False, allow_blank=True, trim_whitespace=False, write_only=True
    )
    full_name = serializers.CharField(max_length=180, required=False, allow_blank=True)


class TeamInvitationPreviewView(NoStoreAccountView):
    permission_classes = [AllowAny]
    throttle_classes = [InvitationIPThrottle, InvitationTokenThrottle]

    def post(self, request):
        data = VerificationTokenSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        invitation = find_invitation(data.validated_data["token"])
        return Response(
            {
                "email": invitation.email,
                "full_name": invitation.full_name,
                "role": invitation.role,
                "role_label": invitation.get_role_display(),
                "workspace_name": str(invitation.organization),
                "expires_at": invitation.expires_at,
                "existing_account": get_user_model()
                .objects.filter(email__iexact=invitation.email)
                .exists(),
            }
        )


class TeamInvitationAcceptView(TeamInvitationPreviewView):
    def post(self, request):
        data = TeamInvitationAcceptSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(accept_team_invitation(request, **data.validated_data))
