import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from apps.audit.services import record_event
from apps.organizations.models import OrganizationMembership
from apps.tenants.models import Tenant

from .access_state import mark_email_verified
from .account_mail import send_account_mail
from .email_verification import NoStoreAccountView, VerificationTokenSerializer, secret_hash
from .models import TenantInvitation
from .security import is_disposable_email, normalize_email

INVALID = "This invitation has expired or is unavailable. Ask your property manager for a new one."


def find_invitation(token):
    invitation = (
        TenantInvitation.objects.select_related("tenant", "organization")
        .filter(token_hash=secret_hash(token))
        .first()
    )
    if (
        not invitation
        or invitation.revoked_at
        or invitation.accepted_at
        or invitation.expires_at <= timezone.now()
        or not invitation.organization.is_active
        or not invitation.tenant.is_active
        or invitation.tenant.user_id
        or invitation.tenant.organization_id != invitation.organization_id
        or normalize_email(invitation.tenant.email) != invitation.email
    ):
        raise ValidationError(INVALID)
    return invitation


@transaction.atomic
def issue_tenant_invitation(request, tenant):
    from apps.subscriptions.catalog import Feature
    from apps.subscriptions.services import require_feature

    require_feature(tenant.organization, Feature.TENANT_PORTAL)
    tenant = Tenant.objects.select_for_update().select_related("organization").get(pk=tenant.pk)
    email = normalize_email(tenant.email)
    if not tenant.is_active or not tenant.organization.is_active or tenant.user_id:
        raise ValidationError("This tenant is unavailable or already has account access.")
    username_limit = get_user_model()._meta.get_field("username").max_length
    if not email or len(email) > username_limit or is_disposable_email(email):
        raise ValidationError(
            {"email": [f"Use a permanent email of {username_limit} characters or fewer."]}
        )
    users = get_user_model().objects.filter(email__iexact=email)
    if (
        users.count() > 1
        or users.filter(is_active=False).exists()
        or users.filter(is_staff=True).exists()
        or users.filter(is_superuser=True).exists()
        or OrganizationMembership.objects.filter(
            user__in=users, is_active=True, role="landlord"
        ).exists()
    ):
        raise ValidationError("This address cannot be used for a tenant account. Contact support.")
    token = secrets.token_urlsafe(32)
    invitation = TenantInvitation.objects.create(
        tenant=tenant,
        organization=tenant.organization,
        email=email,
        token_hash=secret_hash(token),
        expires_at=timezone.now() + timedelta(days=3),
        created_by=request.user,
    )
    link = f"{settings.FRONTEND_URL.rstrip('/')}/accept-invitation?token={token}"
    if not send_account_mail(
        "Your Dwella tenant invitation",
        f"Your property manager invited you to access your tenancy.\n\n{link}\n\n"
        "This invitation expires in 3 days. Existing users must sign in with the invited email. "
        "Accepting an invitation does not sign a lease or make a payment.",
        email,
    ):
        raise ValidationError("The invitation could not be delivered. Please try again.")
    tenant.portal_invitations.filter(accepted_at__isnull=True, revoked_at__isnull=True).exclude(
        pk=invitation.pk
    ).update(revoked_at=timezone.now())
    record_event(request, "tenant.invitation_sent", invitation, tenant.organization)
    return {"sent": True, "expires_at": invitation.expires_at}


@transaction.atomic
def revoke_tenant_invitation(request, tenant):
    tenant = Tenant.objects.select_for_update().get(pk=tenant.pk)
    tenant.portal_invitations.filter(accepted_at__isnull=True, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
    record_event(request, "tenant.invitation_revoked", tenant, tenant.organization)
    return {"revoked": True}


@transaction.atomic
def remove_portal_access(request, tenant):
    """Unlink the tenant's account and withdraw pending invitations.

    Records stay with the tenant. The tenant membership is deleted only when no
    other tenant record in the workspace is linked to the same account, so a
    later invitation can link them again; an administrator's deactivation of a
    membership is left untouched.
    """
    tenant = Tenant.objects.select_for_update().get(pk=tenant.pk)
    tenant.portal_invitations.filter(accepted_at__isnull=True, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
    user_id = tenant.user_id
    if user_id:
        tenant.user = None
        tenant.save(update_fields=["user", "updated_at"])
        if not Tenant.objects.filter(organization=tenant.organization, user_id=user_id).exists():
            OrganizationMembership.objects.filter(
                user_id=user_id, organization=tenant.organization, role="tenant", is_active=True
            ).delete()
    record_event(
        request, "tenant.portal_access_removed", tenant, tenant.organization, account_id=user_id
    )
    return {"removed": bool(user_id)}


@transaction.atomic
def accept_invitation(request, token, password=""):
    candidate = find_invitation(token)
    tenant = Tenant.objects.select_for_update().get(pk=candidate.tenant_id)
    invitation = TenantInvitation.objects.select_for_update().get(pk=candidate.pk)
    find_invitation(token)  # Recheck after the locks, including email and activation.
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
        first, _, last = tenant.full_name.partition(" ")
        if not password:
            raise ValidationError({"password": ["Choose a password for your new account."]})
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
    memberships = OrganizationMembership.objects.filter(user=user, is_active=True)
    if (
        not user.is_active
        or user.is_staff
        or user.is_superuser
        or memberships.exclude(organization=invitation.organization, role="tenant").exists()
    ):
        raise PermissionDenied("This account cannot be linked to this tenant invitation.")
    membership, _ = OrganizationMembership.objects.get_or_create(
        user=user, organization=invitation.organization, defaults={"role": "tenant"}
    )
    if membership.role != "tenant" or not membership.is_active:
        raise PermissionDenied(
            "This account's workspace access cannot be changed by an invitation."
        )
    tenant.user = user
    tenant.save(update_fields=["user", "updated_at"])
    invitation.accepted_at, invitation.accepted_by = timezone.now(), user
    invitation.save(update_fields=["accepted_at", "accepted_by", "updated_at"])
    mark_email_verified(user)
    record_event(
        request,
        "tenant.invitation_accepted",
        invitation,
        invitation.organization,
        account_id=user.pk,
    )
    return {"accepted": True, "sign_in_required": not request.user.is_authenticated}


class InvitationAcceptSerializer(VerificationTokenSerializer):
    password = serializers.CharField(
        max_length=128, required=False, allow_blank=True, trim_whitespace=False, write_only=True
    )


class InvitationIPThrottle(AnonRateThrottle):
    scope = "tenant_invitation_ip"
    rate = "20/hour"


class InvitationWriteThrottle(UserRateThrottle):
    scope = "tenant_invitation_write"
    rate = "20/hour"


class InvitationPreviewView(NoStoreAccountView):
    permission_classes = [AllowAny]

    def get_throttles(self):
        return [*super().get_throttles(), InvitationIPThrottle()]

    def post(self, request):
        data = VerificationTokenSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        invitation = find_invitation(data.validated_data["token"])
        return Response(
            {
                "email": invitation.email,
                "tenant_name": invitation.tenant.full_name,
                "workspace_name": str(invitation.organization),
                "expires_at": invitation.expires_at,
                "existing_account": get_user_model()
                .objects.filter(email__iexact=invitation.email)
                .exists(),
            }
        )


class InvitationAcceptView(InvitationPreviewView):
    def post(self, request):
        data = InvitationAcceptSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(accept_invitation(request, **data.validated_data))
