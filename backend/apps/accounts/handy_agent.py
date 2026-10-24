from datetime import timedelta
from uuid import uuid4

import jwt
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied

from apps.common.permissions import get_active_membership
from apps.common.workspaces import resolve_workspace
from apps.organizations.models import OrganizationMembership


class HandyAgentUnavailable(APIException):
    status_code = 503
    default_detail = "The assistant integration is not configured."
    default_code = "handy_agent_unavailable"


GROUPS_BY_ROLE = {
    OrganizationMembership.Role.LANDLORD: [
        "organization_admin",
        "portfolio_manager",
        "portfolio_viewer",
    ],
}

ACTOR_ROLES = {OrganizationMembership.Role.LANDLORD}


def handy_agent_enabled():
    from apps.audit.models import PlatformSettings

    return PlatformSettings.objects.filter(pk=1, handy_agent_enabled=True).exists()


def token_access(user, request):
    if user.is_staff or user.is_superuser:
        organization = resolve_workspace(request, user=user, required=False)
        return ["platform_admin"], organization

    membership = get_active_membership(user)
    if not membership or not membership.organization.is_active:
        raise PermissionDenied("An active Dwella workspace is required.")
    groups = GROUPS_BY_ROLE.get(membership.role)
    if not groups:
        raise PermissionDenied("The assistant is not available for this account type yet.")
    return groups, membership.organization


def issue_handy_agent_token(user, request):
    if not handy_agent_enabled():
        raise PermissionDenied("The assistant is disabled by the administrator.")
    secret = settings.HANDY_AGENT_SIGNING_SECRET
    if len(secret) < 32:
        raise HandyAgentUnavailable()

    groups, organization = token_access(user, request)
    membership = get_active_membership(user) if organization and not user.is_staff else None
    can_act = bool(membership and membership.role in ACTOR_ROLES)
    issued_at = timezone.now()
    expires_at = issued_at + timedelta(seconds=settings.HANDY_AGENT_TOKEN_TTL_SECONDS)
    display_name = user.get_full_name().strip() or user.email or user.get_username()
    payload = {
        "sub": str(user.pk),
        "name": display_name,
        "groups": groups,
        "agent": {"thinker": True, "actor": can_act, "ledger": False},
        "attrs": {"organization_ids": [organization.pk] if organization else []},
        "aud": settings.HANDY_AGENT_AUDIENCE,
        "iss": settings.HANDY_AGENT_ISSUER,
        "iat": issued_at,
        "exp": expires_at,
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, secret, algorithm="HS256"), expires_at
