from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.html import escape
from django.utils.http import urlsafe_base64_encode
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404

from apps.accounts.security import frontend_reset_url
from apps.marketing.emails import Message, send_message
from apps.organizations.models import Organization, OrganizationMembership

User = get_user_model()


def lock_target(request, user_id):
    """Call inside atomic. Serialize last-superuser and last-owner decisions."""
    list(User.objects.select_for_update().filter(is_superuser=True).order_by("pk"))
    user = get_object_or_404(User.objects.select_for_update(), pk=user_id)
    org_ids = user.organization_memberships.values_list("organization_id", flat=True)
    list(Organization.objects.select_for_update().filter(pk__in=org_ids).order_by("pk"))
    return user


def require_superuser(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Only a platform superuser can perform this action.")


def protect_account(request, user, *, remove_access=False):
    if user.pk == request.user.pk:
        raise ValidationError("You cannot deactivate, demote or delete your own account.")
    if user.is_superuser and not User.objects.filter(
        is_superuser=True, is_active=True,
    ).exclude(pk=user.pk).exists():
        raise ValidationError("The last active superuser must be retained.")
    if remove_access:
        protect_owner(user)


def protect_owner(user, organization=None):
    owners = user.organization_memberships.filter(is_active=True, role="owner")
    if organization:
        owners = owners.filter(organization=organization)
    for membership in owners:
        if not OrganizationMembership.objects.filter(
            organization=membership.organization, role="owner", is_active=True,
            user__is_active=True,
        ).exclude(user=user).exists():
            raise ValidationError("Add another active owner before removing the last owner.")


@transaction.atomic
def change_membership(request, user, organization, role, remove=False):
    user = lock_target(request, user.pk)
    organization = Organization.objects.select_for_update().get(pk=organization.pk)
    if not organization.is_active:
        raise ValidationError("This workspace is suspended.")
    membership = OrganizationMembership.objects.filter(user=user, organization=organization).first()
    if membership and membership.is_active and membership.role == "owner" and (
        remove or role != "owner"
    ):
        protect_owner(user, organization)
    if remove:
        if not membership or not membership.is_active:
            raise ValidationError("This user is not an active member of the workspace.")
        membership.is_active = False
        membership.save(update_fields=["is_active", "updated_at"])
    elif membership:
        membership.role, membership.is_active = role, True
        membership.save(update_fields=["role", "is_active", "updated_at"])
    else:
        membership = OrganizationMembership.objects.create(
            user=user, organization=organization, role=role, invited_by=request.user,
        )
    return membership


def send_access_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    message = Message(
        subject="Your Dwella account", preheader="A secure link to your Dwella account.",
        paragraphs=[f"Hi {escape(user.get_full_name() or user.email)},",
                    "Use the secure link below to set your password and sign in to Dwella."],
        cta_label="Set password", cta_url=frontend_reset_url(uid, token), countdown=False,
    )
    send_message(SimpleNamespace(email=user.email), message)
