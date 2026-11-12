"""The management team of a workspace: who can work on which properties.

Property admins invite people, choose their role, assign whole properties and
remove access. Property managers see who their teammates are and may cover a
teammate's properties for a limited time; every covered change is audited.
"""

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.audit.models import AuditEvent
from apps.audit.services import record_event
from apps.common.pagination import StandardPageNumberPagination
from apps.common.permissions import CanManageOrganization, CanViewPortfolio
from apps.common.property_scope import is_property_admin
from apps.common.workspaces import resolve_workspace
from apps.properties.models import Property

from .models import (
    CoverSession,
    Organization,
    OrganizationMembership,
    PropertyAssignment,
    TeamInvitation,
)

Role = OrganizationMembership.Role
MANAGEMENT = OrganizationMembership.MANAGEMENT_ROLES
INVITATION_DAYS = 3
COVER_DEFAULT_HOURS = 8
COVER_MAX_HOURS = 72
UNAVAILABLE = "This address cannot be invited to manage this workspace. Contact support."


class TeamWriteThrottle(UserRateThrottle):
    scope = "team_write"
    rate = "60/hour"


class TeamInviteThrottle(UserRateThrottle):
    scope = "team_invite"
    rate = "20/hour"


def display_name(user):
    return user.get_full_name().strip() or user.email or user.get_username()


def team(organization):
    return OrganizationMembership.objects.filter(
        organization=organization, role__in=MANAGEMENT, is_active=True, user__is_active=True
    )


def lock_team(organization):
    """Serialize team changes so the last-admin check cannot be raced."""
    Organization.objects.select_for_update().get(pk=organization.pk)


def properties_in(organization, public_ids):
    wanted = set(public_ids)
    rows = list(Property.objects.for_organization(organization).filter(public_id__in=wanted))
    if len(rows) != len(wanted):
        raise ValidationError({"properties": ["Choose properties from this workspace."]})
    return rows


def close_expired_covers(organization):
    for row in CoverSession.objects.filter(
        organization=organization, ended_at__isnull=True, expires_at__lte=timezone.now()
    ):
        row.ended_at = row.expires_at
        row.save(update_fields=["ended_at", "updated_at"])


def end_covers(request, sessions, why):
    for row in sessions.filter(ended_at__isnull=True).select_related("covering_for__user"):
        row.ended_at = min(timezone.now(), row.expires_at)
        row.ended_by = request.user if request.user.is_authenticated else None
        row.save(update_fields=["ended_at", "ended_by", "updated_at"])
        record_event(
            request,
            "cover.ended",
            row,
            row.organization,
            why=why,
            on_behalf_of=row.covering_for.user_id,
            on_behalf_of_name=display_name(row.covering_for.user),
        )


def set_assignments(request, membership, properties):
    """Replace a manager's properties; returns the names added and removed."""
    current = {
        row.property_id: row
        for row in membership.property_assignments.select_related("property")
    }
    wanted = {item.pk: item for item in properties}
    removed = [row.property.name for pk, row in current.items() if pk not in wanted]
    PropertyAssignment.objects.filter(
        membership=membership, property_id__in=set(current) - set(wanted)
    ).delete()
    added = [item for pk, item in wanted.items() if pk not in current]
    PropertyAssignment.objects.bulk_create(
        PropertyAssignment(
            organization=membership.organization,
            membership=membership,
            property=item,
            assigned_by=request.user if request.user.is_authenticated else None,
        )
        for item in added
    )
    return [item.name for item in added], removed


def clear_proof_reviewer(membership):
    Organization.objects.filter(pk=membership.organization_id, proof_reviewer=membership).update(
        proof_reviewer=None
    )


# --- Invitations -----------------------------------------------------------------


@transaction.atomic
def invite_member(request, organization, *, email, full_name, role, properties):
    from apps.accounts.account_mail import send_account_mail
    from apps.accounts.email_verification import secret_hash
    from apps.accounts.security import is_disposable_email, normalize_email

    lock_team(organization)
    email = normalize_email(email)
    limit = get_user_model()._meta.get_field("username").max_length
    if not email or len(email) > limit or is_disposable_email(email):
        raise ValidationError({"email": [f"Use a permanent email of {limit} characters or fewer."]})
    users = get_user_model().objects.filter(email__iexact=email)
    # One account holds one role in one workspace. The same answer is given for
    # every account that cannot join, so this cannot be used to look people up.
    if (
        users.count() > 1
        or users.filter(is_active=False).exists()
        or users.filter(is_staff=True).exists()
        or users.filter(is_superuser=True).exists()
        or OrganizationMembership.objects.filter(user__in=users, is_active=True).exists()
    ):
        raise ValidationError({"email": [UNAVAILABLE]})
    chosen = properties_in(organization, properties) if role == Role.MANAGER else []
    token = secrets.token_urlsafe(32)
    TeamInvitation.objects.filter(
        organization=organization, email=email, accepted_at__isnull=True, revoked_at__isnull=True
    ).update(revoked_at=timezone.now())
    invitation = TeamInvitation.objects.create(
        organization=organization,
        email=email,
        full_name=" ".join(full_name.split())[:180],
        role=role,
        token_hash=secret_hash(token),
        expires_at=timezone.now() + timedelta(days=INVITATION_DAYS),
        created_by=request.user,
    )
    invitation.properties.set(chosen)
    link = f"{settings.FRONTEND_URL.rstrip('/')}/accept-team-invitation?token={token}"
    label = Role(role).label.lower()
    if not send_account_mail(
        f"You are invited to manage {organization} on Dwella",
        f"{display_name(request.user)} invited you to join {organization} as a {label}.\n\n"
        f"{link}\n\nThis invitation expires in {INVITATION_DAYS} days. If you already have a "
        "Dwella account, sign in with this email address first.",
        email,
    ):
        raise ValidationError("The invitation could not be delivered. Please try again.")
    record_event(
        request,
        "team.invitation_sent",
        invitation,
        organization,
        email=email,
        role=role,
        properties=[item.name for item in chosen],
    )
    return invitation


@transaction.atomic
def revoke_invitation(request, organization, public_id):
    invitation = TeamInvitation.objects.select_for_update().filter(
        organization=organization, public_id=public_id
    ).first()
    if not invitation or invitation.accepted_at or invitation.revoked_at:
        raise ValidationError("This invitation is no longer pending.")
    invitation.revoked_at = timezone.now()
    invitation.save(update_fields=["revoked_at", "updated_at"])
    record_event(
        request, "team.invitation_revoked", invitation, organization, email=invitation.email
    )


# --- Members ---------------------------------------------------------------------


def member_for_update(organization, public_id):
    member = (
        team(organization)
        .select_for_update(of=("self",))
        .select_related("user")
        .filter(public_id=public_id)
        .first()
    )
    if member is None:
        raise ValidationError("This person is not on the team.")
    return member


def require_another_admin(organization, member):
    if not team(organization).filter(role=Role.LANDLORD).exclude(pk=member.pk).exists():
        raise ValidationError("A workspace needs at least one property admin.")


@transaction.atomic
def update_member(request, organization, public_id, *, role=None, properties=None):
    lock_team(organization)
    member = member_for_update(organization, public_id)
    changes = {}
    if role and role != member.role:
        if member.user_id == request.user.pk:
            raise PermissionDenied("Ask another property admin to change your own role.")
        if member.role == Role.LANDLORD:
            require_another_admin(organization, member)
        changes["role"] = {"from": member.role, "to": role}
        member.role = role
        member.save(update_fields=["role", "updated_at"])
        if role == Role.LANDLORD:
            # An admin needs no assignments and never works under a cover.
            properties = []
            end_covers(request, CoverSession.objects.filter(manager=member), "role_changed")
        else:
            clear_proof_reviewer(member)
    if member.role == Role.LANDLORD and properties:
        raise ValidationError({"properties": ["A property admin already sees every property."]})
    if properties is not None:
        added, removed = set_assignments(
            request, member, properties_in(organization, properties)
        )
        if added or removed:
            changes["properties"] = {"added": added, "removed": removed}
    if changes:
        record_event(
            request,
            "team.member_changed",
            member,
            organization,
            member=member.user_id,
            member_name=display_name(member.user),
            **changes,
        )
    return member


@transaction.atomic
def remove_member(request, organization, public_id):
    lock_team(organization)
    member = member_for_update(organization, public_id)
    if member.user_id == request.user.pk:
        raise PermissionDenied("Ask another property admin to remove you.")
    if member.role == Role.LANDLORD:
        require_another_admin(organization, member)
    end_covers(
        request,
        CoverSession.objects.filter(organization=organization).filter(
            Q(manager=member) | Q(covering_for=member)
        ),
        "member_removed",
    )
    member.property_assignments.all().delete()
    clear_proof_reviewer(member)
    member.is_active = False
    member.save(update_fields=["is_active", "updated_at"])
    record_event(
        request,
        "team.member_removed",
        member,
        organization,
        member=member.user_id,
        member_name=display_name(member.user),
        role=member.role,
    )


# --- Cover -----------------------------------------------------------------------


def own_membership(request, organization):
    return team(organization).filter(user=request.user).select_related("user").first()


@transaction.atomic
def start_cover(request, organization, *, teammate, reason, hours):
    lock_team(organization)
    organization.refresh_from_db(fields=["allow_teammate_cover"])
    if not organization.allow_teammate_cover:
        raise PermissionDenied("Covering for teammates is switched off for this workspace.")
    me = own_membership(request, organization)
    if not me or me.role != Role.MANAGER:
        raise PermissionDenied("Only a property manager can cover for a teammate.")
    other = (
        team(organization)
        .filter(public_id=teammate, role=Role.MANAGER)
        .exclude(pk=me.pk)
        .select_related("user")
        .first()
    )
    if other is None:
        raise ValidationError({"teammate": ["Choose a property manager on your team."]})
    close_expired_covers(organization)
    if CoverSession.objects.filter(manager=me, ended_at__isnull=True).exists():
        raise ValidationError("End your current cover before starting another.")
    cover = CoverSession.objects.create(
        organization=organization,
        manager=me,
        covering_for=other,
        reason=reason,
        expires_at=timezone.now() + timedelta(hours=hours),
    )
    record_event(
        request,
        "cover.started",
        cover,
        organization,
        on_behalf_of=other.user_id,
        on_behalf_of_name=display_name(other.user),
        reason=reason,
        hours=hours,
    )
    return cover


@transaction.atomic
def end_cover(request, organization, public_id=None):
    """A manager ends their own cover; an admin may end anyone's."""
    sessions = CoverSession.objects.select_for_update(of=("self",)).filter(
        organization=organization, ended_at__isnull=True, expires_at__gt=timezone.now()
    )
    if public_id is None:
        sessions = sessions.filter(manager__user=request.user)
    else:
        sessions = sessions.filter(public_id=public_id)
        if not is_property_admin(request):
            sessions = sessions.filter(manager__user=request.user)
    if not sessions.exists():
        raise ValidationError("There is no open cover to end.")
    end_covers(request, sessions, "ended")


# --- Representation --------------------------------------------------------------


def cover_data(row):
    return {
        "id": str(row.public_id),
        "manager": {"id": str(row.manager.public_id), "name": display_name(row.manager.user)},
        "covering_for": {
            "id": str(row.covering_for.public_id),
            "name": display_name(row.covering_for.user),
        },
        "reason": row.reason,
        "started_at": row.created_at,
        "expires_at": row.expires_at,
    }


def open_covers(organization):
    return CoverSession.objects.filter(
        organization=organization, ended_at__isnull=True, expires_at__gt=timezone.now()
    ).select_related("manager__user", "covering_for__user")


def team_payload(request, organization):
    admin = is_property_admin(request)
    members = list(
        team(organization)
        .select_related("user")
        .prefetch_related("property_assignments__property")
        .order_by("role", "user__first_name", "user__email")
    )
    covers = list(open_covers(organization))
    data = {
        "can_manage": admin,
        "allow_teammate_cover": organization.allow_teammate_cover,
        "members": [
            {
                "id": str(member.public_id),
                "name": display_name(member.user),
                # Teammates see names and properties; contact details are for admins.
                "email": member.user.email if admin or member.user_id == request.user.pk else "",
                "role": member.role,
                "role_label": member.get_role_display(),
                "is_you": member.user_id == request.user.pk,
                "joined_at": member.created_at,
                "properties": [
                    {"id": str(row.property.public_id), "name": row.property.name}
                    for row in member.property_assignments.all()
                ],
            }
            for member in members
        ],
        "covers": [cover_data(row) for row in covers],
        "invitations": [],
    }
    if admin:
        pending = (
            TeamInvitation.objects.filter(
                organization=organization,
                accepted_at__isnull=True,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            )
            .prefetch_related("properties")
            .order_by("-created_at")
        )
        data["invitations"] = [
            {
                "id": str(row.public_id),
                "email": row.email,
                "name": row.full_name,
                "role": row.role,
                "role_label": row.get_role_display(),
                "expires_at": row.expires_at,
                "properties": [
                    {"id": str(item.public_id), "name": item.name} for item in row.properties.all()
                ],
            }
            for row in pending
        ]
    return data


# --- API -------------------------------------------------------------------------


class RoleField(serializers.ChoiceField):
    def __init__(self, **kwargs):
        super().__init__(choices=[Role.LANDLORD, Role.MANAGER], **kwargs)


class PropertiesField(serializers.ListField):
    def __init__(self, **kwargs):
        super().__init__(child=serializers.UUIDField(), max_length=500, **kwargs)


class InviteSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    full_name = serializers.CharField(max_length=180, required=False, allow_blank=True, default="")
    role = RoleField()
    properties = PropertiesField(required=False, default=list)


class MemberSerializer(serializers.Serializer):
    role = RoleField(required=False)
    properties = PropertiesField(required=False)


class SettingsSerializer(serializers.Serializer):
    allow_teammate_cover = serializers.BooleanField()


class CoverSerializer(serializers.Serializer):
    teammate = serializers.UUIDField()
    reason = serializers.CharField(min_length=5, max_length=300)
    hours = serializers.IntegerField(
        min_value=1, max_value=COVER_MAX_HOURS, required=False, default=COVER_DEFAULT_HOURS
    )


def valid(serializer_class, request, **kwargs):
    serializer = serializer_class(data=request.data, **kwargs)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


class TeamBaseView(APIView):
    """Reads are for the whole management team; changes are for property admins."""

    admin_methods = frozenset({"POST", "PATCH", "PUT", "DELETE"})
    throttle_class = TeamWriteThrottle

    def get_permissions(self):
        admin = self.request.method in self.admin_methods
        return [CanManageOrganization() if admin else CanViewPortfolio()]

    def get_throttles(self):
        if self.request.method in {"POST", "PATCH", "PUT", "DELETE"}:
            return [*super().get_throttles(), self.throttle_class()]
        return super().get_throttles()

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response

    def team_response(self, status=200):
        organization = resolve_workspace(self.request)
        return Response(team_payload(self.request, organization), status=status)


class TeamView(TeamBaseView):
    def get(self, request):
        close_expired_covers(resolve_workspace(request))
        return self.team_response()

    def patch(self, request):
        organization = resolve_workspace(request)
        data = valid(SettingsSerializer, request)
        with transaction.atomic():
            lock_team(organization)
            organization.allow_teammate_cover = data["allow_teammate_cover"]
            organization.save(update_fields=["allow_teammate_cover", "updated_at"])
            if not organization.allow_teammate_cover:
                end_covers(
                    request, CoverSession.objects.filter(organization=organization), "switched_off"
                )
            record_event(
                request,
                "team.cover_setting_changed",
                organization=organization,
                allow_teammate_cover=organization.allow_teammate_cover,
            )
        return self.team_response()


class TeamInvitationsView(TeamBaseView):
    throttle_class = TeamInviteThrottle

    def post(self, request):
        invite_member(request, resolve_workspace(request), **valid(InviteSerializer, request))
        return self.team_response(status=201)


class TeamInvitationRevokeView(TeamBaseView):
    def post(self, request, public_id):
        revoke_invitation(request, resolve_workspace(request), public_id)
        return self.team_response()


class TeamMemberView(TeamBaseView):
    def patch(self, request, public_id):
        update_member(
            request, resolve_workspace(request), public_id, **valid(MemberSerializer, request)
        )
        return self.team_response()

    def delete(self, request, public_id):
        remove_member(request, resolve_workspace(request), public_id)
        return self.team_response()


class CoverView(TeamBaseView):
    # Managers start and end their own cover, so these are not admin-only.
    admin_methods = frozenset()

    def get_permissions(self):
        return [CanViewPortfolio()]

    def post(self, request):
        if request.user.is_staff or request.user.is_superuser:
            raise PermissionDenied("Only a property manager can cover for a teammate.")
        start_cover(request, resolve_workspace(request), **valid(CoverSerializer, request))
        return self.team_response(status=201)

    def delete(self, request, public_id=None):
        end_cover(request, resolve_workspace(request), public_id)
        return self.team_response()


TEAM_ACTIONS = ("team.", "cover.")


class TeamActivityView(TeamBaseView):
    """What changed on the team, and what was done under a cover."""

    def get(self, request):
        organization = resolve_workspace(request)
        events = AuditEvent.objects.filter(organization=organization).filter(
            Q(action__startswith="team.") | Q(action__startswith="cover.")
        )
        if not is_property_admin(request):
            # A manager sees covers they made and covers made for them.
            events = events.filter(action__startswith="cover.").filter(
                Q(actor=request.user) | Q(metadata__on_behalf_of=request.user.pk)
            )
        paginator = StandardPageNumberPagination()
        page = paginator.paginate_queryset(
            events.select_related("actor").order_by("-created_at", "-pk"), request, view=self
        )
        property_ids = {pk for row in page for pk in row.metadata.get("property_ids", [])}
        names = dict(
            Property.objects.for_organization(organization)
            .filter(pk__in=property_ids)
            .values_list("pk", "name")
        )
        keep = (
            "on_behalf_of_name", "reason", "member_name", "email", "role", "properties",
            "url_name", "method", "hours", "why", "allow_teammate_cover",
        )
        return paginator.get_paginated_response([
            {
                "id": str(row.public_id),
                "action": row.action,
                "actor": display_name(row.actor) if row.actor else "Dwella",
                "created_at": row.created_at,
                "property_names": [
                    names[pk] for pk in row.metadata.get("property_ids", []) if pk in names
                ],
                "details": {key: row.metadata[key] for key in keep if key in row.metadata},
            }
            for row in page
        ])
