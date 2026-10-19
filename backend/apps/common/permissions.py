from rest_framework.permissions import BasePermission

from apps.organizations.models import OrganizationMembership

PORTFOLIO_ROLES = {
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.MANAGER,
    OrganizationMembership.Role.STAFF,
    OrganizationMembership.Role.VIEWER,
}

PORTFOLIO_MANAGER_ROLES = {
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.MANAGER,
}


def get_active_membership(user):
    if not user or not user.is_authenticated:
        return None
    return (
        user.organization_memberships.filter(is_active=True)
        .select_related("organization")
        .order_by("created_at")
        .first()
    )


def get_user_access(user):
    if user.is_superuser or user.is_staff:
        return {
            "persona": "platform_admin",
            "role": "platform_admin",
            "organization_id": None,
            "can_view_portfolio": True,
            "can_manage_properties": False,
            "can_view_reports": True,
            "can_manage_organization": True,
        }

    membership = get_active_membership(user)
    role = membership.role if membership else None
    persona = (
        "tenant"
        if role == OrganizationMembership.Role.TENANT
        else "landlord"
        if role
        else "unassigned"
    )
    return {
        "persona": persona,
        "role": role or "unassigned",
        "organization_id": str(membership.organization.public_id) if membership else None,
        "can_view_portfolio": role in PORTFOLIO_ROLES,
        "can_manage_properties": role in PORTFOLIO_MANAGER_ROLES,
        "can_view_reports": role in PORTFOLIO_ROLES,
        "can_manage_organization": role in {
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
        },
    }


class IsOrganizationMember(BasePermission):
    message = "You must belong to this organization."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or get_active_membership(request.user))
        )

    def has_object_permission(self, request, view, obj):
        organization = getattr(obj, "organization", obj)
        memberships = getattr(request.user, "organization_memberships", None)
        if memberships is None:
            return False
        return memberships.filter(organization=organization, is_active=True).exists()


class CanViewPortfolio(BasePermission):
    message = "You do not have permission to view this portfolio."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and get_user_access(request.user)["can_view_portfolio"]
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        organization = getattr(obj, "organization", obj)
        membership = get_active_membership(request.user)
        return bool(
            membership
            and membership.organization_id == organization.id
            and membership.role in PORTFOLIO_ROLES
        )


class CanManagePortfolio(BasePermission):
    message = "Only a landlord or portfolio manager can make this change."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and get_user_access(request.user)["can_manage_properties"]
        )

    def has_object_permission(self, request, view, obj):
        organization = getattr(obj, "organization", obj)
        membership = get_active_membership(request.user)
        return bool(
            membership
            and membership.organization_id == organization.id
            and membership.role in PORTFOLIO_MANAGER_ROLES
        )
