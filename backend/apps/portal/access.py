"""Which tenancy records a signed-in tenant may see.

A tenant account reaches records only through `Tenant.user`, set when the
tenant accepts a manager's invitation. Being a tenant member of a workspace is
not enough on its own: the manager must have linked a tenant record to them.
"""

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from apps.common.workspaces import resolve_workspace
from apps.organizations.models import OrganizationMembership
from apps.subscriptions.catalog import Feature
from apps.subscriptions.services import require_feature
from apps.tenants.models import Tenant

NOT_LINKED = {
    "message": "Your account is not linked to a tenancy yet. Ask your property manager "
    "to send you an invitation.",
    "code": "tenancy_not_linked",
}


class PortalContext:
    def __init__(self, organization, tenants):
        self.organization = organization
        self.tenants = tenants
        self.tenant_ids = [tenant.pk for tenant in tenants]

    def scope(self, queryset):
        return queryset.filter(organization=self.organization, tenant_id__in=self.tenant_ids)


def portal_context(request):
    cached = getattr(request, "_portal_context", None)
    if cached and cached[0] == request.user.pk:
        return cached[1]
    user = request.user
    if user.is_staff or user.is_superuser:
        raise PermissionDenied("The tenant portal is for tenant accounts.")
    organization = resolve_workspace(request)  # Checks mailbox proof and suspension.
    membership = getattr(request, "_workspace_membership", (None, None))[1]
    if (
        organization is None
        or membership is None
        or membership.role != OrganizationMembership.Role.TENANT
    ):
        raise PermissionDenied("The tenant portal is for tenant accounts.")
    require_feature(organization, Feature.TENANT_PORTAL)
    tenants = list(
        Tenant.objects.filter(organization=organization, user=user, is_active=True).order_by(
            "created_at"
        )
    )
    if not tenants:
        raise PermissionDenied(NOT_LINKED)
    context = PortalContext(organization, tenants)
    request._portal_context = (user.pk, context)
    return context


class IsPortalTenant(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(portal_context(request))
