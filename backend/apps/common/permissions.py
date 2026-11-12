from rest_framework.permissions import BasePermission

from apps.organizations.models import OrganizationMembership

from .workspaces import resolve_workspace

# Platform super admins (is_superuser) sit outside workspaces. Inside one, a
# property admin (stored as `landlord`) oversees everything, a property manager
# works on assigned properties, and tenants use the tenant portal. Which
# properties a manager reaches is decided in property_scope, not here.
PORTFOLIO_ROLES = set(OrganizationMembership.MANAGEMENT_ROLES)

PORTFOLIO_MANAGER_ROLES = set(OrganizationMembership.MANAGEMENT_ROLES)


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
    from apps.accounts.access_state import email_status

    verified_access = not email_status(user, request)["required"]
    if user.is_superuser or user.is_staff:
        organization = resolve_workspace(request, required=False) if request else None
        session = getattr(request, "support_session", None) if request else None
        return access_representation(
            user, verified_access=verified_access, organization=organization, session=session
        )

    # Reuse the membership resolve_workspace already read for this request.
    resolved = getattr(request, "_workspace_membership", None) if request is not None else None
    membership = resolved[1] if resolved and resolved[0] == user.pk else get_active_membership(user)
    from apps.accounts.models import AccountAccessState

    removed = (
        not membership
        and AccountAccessState.objects.filter(user=user, tenant_access_removed=True).exists()
    )
    return access_representation(
        user,
        membership=membership,
        verified_access=verified_access,
        tenant_access_removed=bool(removed),
    )


def access_representation(
    user,
    *,
    membership=None,
    verified_access=True,
    organization=None,
    session=None,
    tenant_access_removed=False,
):
    """Display access from supplied records, without performing authorization reads."""
    if user.is_superuser or user.is_staff:
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
            "can_view_portfolio": bool(organization and verified_access),
            "can_manage_properties": bool(organization and verified_access),
            "can_view_reports": bool(organization and verified_access),
            "can_manage_organization": bool(organization and verified_access),
            "is_property_admin": bool(organization and verified_access),
            "property_scope": "all",
        }

    role = membership.role if membership else None
    available = bool(membership and membership.organization.is_active and verified_access)
    persona = (
        "tenant"
        if role == OrganizationMembership.Role.TENANT
        else "landlord"
        if role in PORTFOLIO_ROLES
        else "unassigned"
    )
    # Both management roles use the manager app; `role` tells them apart.
    admin = available and role == OrganizationMembership.Role.LANDLORD
    return {
        "persona": persona,
        "tenant_access_removed": bool(tenant_access_removed),
        "acting_workspace": None,
        "workspace_suspended": bool(membership and not membership.organization.is_active),
        "role": role or "unassigned",
        "organization_id": str(membership.organization.public_id) if membership else None,
        "can_view_portfolio": available and role in PORTFOLIO_ROLES,
        "can_manage_properties": available and role in PORTFOLIO_MANAGER_ROLES,
        "can_view_reports": available and role in PORTFOLIO_ROLES,
        "can_manage_organization": admin,
        "is_property_admin": admin,
        "property_scope": "all" if admin else "assigned" if role in PORTFOLIO_ROLES else "none",
    }


class IsPlatformAdmin(BasePermission):
    message = "Platform administrator access is required."

    def has_permission(self, request, view):
        from apps.accounts.access_state import require_verified_access

        if request.user and request.user.is_authenticated:
            require_verified_access(request.user, request)
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class IsPlatformSuperuser(BasePermission):
    message = "Platform superuser access is required."

    def has_permission(self, request, view):
        from apps.accounts.access_state import require_verified_access

        if request.user and request.user.is_authenticated:
            require_verified_access(request.user, request)
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
    message = "You do not have permission to make this change."
    access_key = "can_manage_properties"
    roles = PORTFOLIO_MANAGER_ROLES


class CanManageOrganization(WorkspacePermission):
    message = "Only a property admin of this workspace can do this."
    access_key = "can_manage_organization"

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return super().has_object_permission(request, view, obj)
        organization = getattr(obj, "organization", obj)
        return request.user.organization_memberships.filter(
            organization=organization, is_active=True, role=OrganizationMembership.Role.LANDLORD
        ).exists()
