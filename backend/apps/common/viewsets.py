from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS

from .permissions import CanManagePortfolio, CanViewPortfolio
from .workspaces import resolve_workspace


class OrganizationScopedModelViewSet(viewsets.ModelViewSet):
    permission_classes = [CanViewPortfolio]
    lookup_field = "public_id"
    lookup_url_kwarg = "public_id"

    def get_organization(self):
        return resolve_workspace(self.request)

    def get_permissions(self):
        # Keyed on the HTTP method rather than the action name so custom
        # write actions (`@action(methods=["post"])`) need manage rights too.
        permission_classes = (
            [CanViewPortfolio] if self.request.method in SAFE_METHODS else [CanManagePortfolio]
        )
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .for_organization(self.get_organization())
            .select_related("organization")
        )

    def perform_create(self, serializer):
        serializer.save(organization=self.get_organization())
