from dataclasses import dataclass

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.handy_agent import ACTOR_ROLES, handy_agent_enabled
from apps.organizations.models import OrganizationMembership

User = get_user_model()


@dataclass(frozen=True)
class HandyAgentPrincipal:
    claims: dict
    organization: object

    @property
    def jti(self):
        return self.claims["jti"]


class HandyAgentAuthentication(BaseAuthentication):
    """Authenticate action calls without exposing Handy tokens to normal APIs."""

    keyword = b"bearer"

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header:
            return None
        if len(header) != 2 or header[0].lower() != self.keyword:
            raise AuthenticationFailed("Use a Bearer token for assistant actions.")
        if not handy_agent_enabled():
            raise AuthenticationFailed("The assistant is disabled by the administrator.")

        secret = settings.HANDY_AGENT_SIGNING_SECRET
        if len(secret) < 32:
            raise AuthenticationFailed("The assistant integration is unavailable.")
        try:
            claims = jwt.decode(
                header[1],
                secret,
                algorithms=["HS256"],
                audience=settings.HANDY_AGENT_AUDIENCE,
                issuer=settings.HANDY_AGENT_ISSUER,
                options={"require": ["sub", "exp", "iat", "jti", "agent", "attrs"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationFailed("The assistant token is invalid or expired.") from exc

        if claims.get("agent", {}).get("actor") is not True:
            raise AuthenticationFailed("This assistant token cannot perform actions.")
        organization_ids = claims.get("attrs", {}).get("organization_ids")
        if not isinstance(organization_ids, list) or len(organization_ids) != 1:
            raise AuthenticationFailed("The assistant token has no active workspace.")

        try:
            user = User.objects.get(pk=claims["sub"], is_active=True)
        except (User.DoesNotExist, ValueError, TypeError) as exc:
            raise AuthenticationFailed("The assistant user is no longer active.") from exc

        membership = (
            OrganizationMembership.objects.select_related("organization")
            .filter(
                user=user,
                organization_id=organization_ids[0],
                organization__is_active=True,
                is_active=True,
                role__in=ACTOR_ROLES,
            )
            .first()
        )
        if membership is None:
            raise AuthenticationFailed("Assistant action permission is no longer available.")

        request.organization = membership.organization
        raw_request = getattr(request, "_request", request)
        raw_request.organization = membership.organization
        return user, HandyAgentPrincipal(claims=claims, organization=membership.organization)

    def authenticate_header(self, request):
        return 'Bearer realm="dwella-assistant"'
