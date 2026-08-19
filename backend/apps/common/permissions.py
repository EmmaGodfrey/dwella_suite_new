from rest_framework.permissions import BasePermission


class IsOrganizationMember(BasePermission):
    message = "You must belong to this organization."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        organization = getattr(obj, "organization", obj)
        memberships = getattr(request.user, "organization_memberships", None)
        if memberships is None:
            return False
        return memberships.filter(organization=organization, is_active=True).exists()
