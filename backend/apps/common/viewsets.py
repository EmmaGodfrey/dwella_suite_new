from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS

from .permissions import CanManageOrganization, CanManagePortfolio, CanViewPortfolio
from .property_scope import property_scope, require_in_scope
from .workspaces import resolve_workspace


class OrganizationScopedModelViewSet(viewsets.ModelViewSet):
    permission_classes = [CanViewPortfolio]
    lookup_field = "public_id"
    lookup_url_kwarg = "public_id"
    # False for records the whole management team shares, such as vendors.
    # Everything else is narrowed to the properties the person may work on.
    property_scoped = True
    # Actions only a property admin may take, whatever the HTTP method.
    admin_only_actions = frozenset()

    def get_organization(self):
        return resolve_workspace(self.request)

    def get_permissions(self):
        # Keyed on the HTTP method rather than the action name so custom
        # write actions (`@action(methods=["post"])`) need manage rights too.
        permission_classes = (
            [CanViewPortfolio] if self.request.method in SAFE_METHODS else [CanManagePortfolio]
        )
        if getattr(self, "action", None) in self.admin_only_actions:
            permission_classes = [CanManageOrganization]
        return [permission() for permission in permission_classes]

    def get_property_scope(self):
        return property_scope(self.request)

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .for_organization(self.get_organization())
            .select_related("organization")
        )
        if self.property_scoped:
            queryset = self.get_property_scope().filter(queryset)
        return queryset

    def get_object(self):
        instance = super().get_object()
        if self.property_scoped and self.request.method not in SAFE_METHODS:
            require_in_scope(self.request, instance)
        return instance

    # The queryset and the serializers' related fields already keep a manager
    # inside their properties. These checks run after the save as a second
    # fence: a record created in, or moved to, another property is refused and
    # the request's transaction rolls the write back.
    def perform_create(self, serializer):
        instance = serializer.save(organization=self.get_organization())
        if self.property_scoped:
            self.check_saved(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        if self.property_scoped:
            self.check_saved(instance)

    def check_saved(self, instance):
        require_in_scope(self.request, instance)
