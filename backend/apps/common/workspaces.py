"""Single authoritative organization context for all portfolio APIs."""

from uuid import UUID

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError


def resolve_workspace(request, *, user=None, required=True):
    user = user if user is not None else request.user
    if not user or not user.is_authenticated:
        return None
    if not getattr(request, "_workspace_resolved", False):
        organization, session = None, None
        if user.is_staff or user.is_superuser:
            header = request.headers.get("X-Dwella-Workspace")
            # Account/lifecycle operations must remain usable with stale browser state.
            # /me/ still reports a valid optional context for the workspace banner.
            path = request.path_info
            if path.startswith("/api/v1/platform/") or (
                path.startswith("/api/v1/accounts/") and path != "/api/v1/accounts/me/"
            ):
                header = None
            if header is not None:
                from apps.audit.models import SupportSession

                try:
                    workspace_id = UUID(header)
                except (ValueError, TypeError, AttributeError):
                    request._workspace_error = "Invalid workspace support session."
                else:
                    session = (
                        SupportSession.objects.select_for_update()
                        .select_related("organization")
                        .filter(
                            admin=user,
                            organization__public_id=workspace_id,
                            ended_at__isnull=True,
                            expires_at__gt=timezone.now(),
                        )
                        .first()
                    )
                    if session is None:
                        request._workspace_error = "Workspace support session has expired or ended."
                    else:
                        organization = session.organization
        else:
            from .permissions import get_active_membership

            membership = get_active_membership(user)
            organization = membership.organization if membership else None
        request.organization = organization
        request.support_session = session
        request._workspace_resolved = True
        # Django middleware receives the underlying request after DRF returns.
        raw = getattr(request, "_request", request)
        raw.organization = organization
        raw.support_session = session
    organization = getattr(request, "organization", None)
    if required and organization is None and (user.is_staff or user.is_superuser):
        if error := getattr(request, "_workspace_error", None):
            raise PermissionDenied(error)
        raise ValidationError("Choose a workspace first.")
    return organization
