"""Single authoritative organization context for all portfolio APIs."""

from uuid import UUID

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import SAFE_METHODS


def is_workspace_scoped(request):
    return request.path_info.startswith(tuple(
        f"/api/v1/{area}/" for area in (
            "properties", "tenants", "leases", "billing", "reports", "notifications",
            "organizations", "maintenance", "integrations", "documents", "subscriptions",
        )
    ))


def _active_session(user, workspace_id, *, lock=False):
    from apps.audit.models import SupportSession

    query = SupportSession.objects.select_related("organization").filter(
        admin=user, organization__public_id=workspace_id, organization__is_active=True,
        ended_at__isnull=True, expires_at__gt=timezone.now(),
    )
    if lock:
        # Do not lock the joined organization or serialize parallel read requests.
        query = query.select_for_update(of=("self",))
    return query.first()


def resolve_workspace(request, *, user=None, required=True):
    user = user if user is not None else request.user
    if not user or not user.is_authenticated:
        return None
    if required:
        from apps.accounts.access_state import require_verified_access

        require_verified_access(user, request)
    if not getattr(request, "_workspace_resolved", False):
        organization, session = None, None
        if user.is_staff or user.is_superuser:
            header = request.headers.get("X-Dwella-Workspace")
            # Account/lifecycle operations must remain usable with stale browser state.
            # /me/ still reports a valid optional context for the workspace banner.
            path = request.path_info
            if not is_workspace_scoped(request) and path != "/api/v1/accounts/me/":
                header = None
            if header is not None:
                try:
                    workspace_id = UUID(header)
                except (ValueError, TypeError, AttributeError):
                    request._workspace_error = "Invalid workspace support session."
                else:
                    session = _active_session(user, workspace_id)
                    if session is None:
                        request._workspace_error = "Workspace support session has expired or ended."
                    else:
                        organization = session.organization
        else:
            from .permissions import get_active_membership

            membership = get_active_membership(user)
            organization = membership.organization if membership else None
            request._workspace_membership = (user.pk, membership)
        request.organization, request.support_session = organization, session
        request._workspace_resolved = True

    session = getattr(request, "support_session", None)
    if (
        required and session and request.method not in SAFE_METHODS
        and not getattr(request, "_workspace_locked", False)
    ):
        # Authentication only performs an optional read. Re-check after taking the
        # write lock, so ending/expiring between authentication and permission fails.
        session = _active_session(user, session.organization.public_id, lock=True)
        request.support_session = session
        request.organization = session.organization if session else None
        request._workspace_locked = True
        if session is None:
            request._workspace_error = "Workspace support session has expired or ended."

    if getattr(request, "_workspace_resolved", False):
        # Django middleware receives the underlying request after DRF returns.
        raw = getattr(request, "_request", request)
        raw.organization = request.organization
        raw.support_session = request.support_session
    organization = getattr(request, "organization", None)
    if required and organization is not None and not organization.is_active:
        raise PermissionDenied("This workspace is suspended. Contact Dwella support.")
    if required and organization is None and (user.is_staff or user.is_superuser):
        if error := getattr(request, "_workspace_error", None):
            raise PermissionDenied(error)
        raise ValidationError("Choose a workspace first.")
    return organization
