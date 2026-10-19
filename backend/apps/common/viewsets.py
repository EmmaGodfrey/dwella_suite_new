from rest_framework import viewsets

from .permissions import CanManagePortfolio, CanViewPortfolio, get_active_membership


class OrganizationScopedModelViewSet(viewsets.ModelViewSet):
    permission_classes = [CanViewPortfolio]
    lookup_field = "public_id"
    lookup_url_kwarg = "public_id"

    def get_organization(self):
        organization = getattr(self.request, "organization", None)
        if organization is not None:
            return organization

        membership = get_active_membership(self.request.user)
        return membership.organization if membership else None

    def get_permissions(self):
        permission_classes = (
            [CanManagePortfolio]
            if self.action in {"create", "update", "partial_update", "destroy"}
            else [CanViewPortfolio]
        )
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().for_organization(self.get_organization())

    def perform_create(self, serializer):
        serializer.save(organization=self.get_organization())
