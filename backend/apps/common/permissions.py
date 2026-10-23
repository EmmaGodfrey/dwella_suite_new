from rest_framework.permissions import BasePermission

from apps.organizations.models import OrganizationMembership

from .workspaces import resolve_workspace

# Dwella has three account types: platform super admins (is_superuser), and
# landlords and tenants inside a workspace. Only landlords see the portfolio.
PORTFOLIO_ROLES = {OrganizationMembership.Role.LANDLORD}

PORTFOLIO_MANAGER_ROLES = {OrganizationMembership.Role.LANDLORD}


def get_active_membership(user):
    if not user or not user.is_authenticated:
        return None
    return (
        user.organization_memberships.filter(is_active=True)
        .select_related("organization")
        .order_by("created_at")
        .first()
    )


def get_user_access(user, request=None):
    if user.is_superuser or user.is_staff:
        organization = resolve_workspace(request, required=False) if request else None
        session = getattr(request, "support_session", None) if request else None
        return {
            "persona": "platform_admin",
            "role": "platform_admin",
            "organization_id": str(organization.public_id) if organization else None,
            "acting_workspace": {
                "id": str(organization.public_id),
                "name": str(organization),
                "session_id": str(session.public_id),
                "reason": session.reason,
                "expires_at": session.expires_at,
            }
            if session
            else None,
            "can_view_portfolio": bool(organization),
            "can_manage_properties": bool(organization),
            "can_view_reports": bool(organization),
            "can_manage_organization": bool(organization),
        }

    membership = get_active_membership(user)
    role = membership.role if membership else None
    available = bool(membership and membership.organization.is_active)
    persona = (
        "tenant"
        if role == OrganizationMembership.Role.TENANT
        else "landlord"
        if role
        else "unassigned"
    )
    return {
        "persona": persona,
        "acting_workspace": None,
        "workspace_suspended": bool(membership and not available),
        "role": role or "unassigned",
        "organization_id": str(membership.organization.public_id) if membership else None,
        "can_view_portfolio": available and role in PORTFOLIO_ROLES,
        "can_manage_properties": available and role in PORTFOLIO_MANAGER_ROLES,
        "can_view_reports": available and role in PORTFOLIO_ROLES,
        "can_manage_organization": available and role == OrganizationMembership.Role.LANDLORD,
    }


class IsPlatformAdmin(BasePermission):
    message = "Platform administrator access is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class IsPlatformSuperuser(BasePermission):
    message = "Platform superuser access is required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class WorkspacePermission(BasePermission):
    access_key = "can_view_portfolio"
    roles = PORTFOLIO_ROLES

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        resolve_workspace(request)
        return get_user_access(request.user, request)[self.access_key]

    def has_object_permission(self, request, view, obj):
        organization = getattr(obj, "organization", obj)
        resolved = resolve_workspace(request)
        return bool(
            resolved and organization.pk == resolved.pk and self.has_permission(request, view)
        )


class IsOrganizationMember(WorkspacePermission):
    message = "You must belong to this organization."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and resolve_workspace(request))

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return super().has_object_permission(request, view, obj)
        organization = getattr(obj, "organization", obj)
        return request.user.organization_memberships.filter(
            organization=organization, is_active=True
        ).exists()


class CanViewPortfolio(WorkspacePermission):
    message = "You do not have permission to view this portfolio."


class CanManagePortfolio(WorkspacePermission):
    message = "Only a landlord can make this change."
    access_key = "can_manage_properties"
    roles = PORTFOLIO_MANAGER_ROLES


class CanManageOrganization(WorkspacePermission):
    message = "Only a landlord of this workspace can change this."
    access_key = "can_manage_organization"

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return super().has_object_permission(request, view, obj)
        organization = getattr(obj, "organization", obj)
        return request.user.organization_memberships.filter(
            organization=organization, is_active=True, role=OrganizationMembership.Role.LANDLORD
        ).exists()
