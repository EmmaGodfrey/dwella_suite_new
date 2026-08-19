from rest_framework import viewsets

from .permissions import IsOrganizationMember


class OrganizationScopedModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOrganizationMember]
    lookup_field = "public_id"
    lookup_url_kwarg = "public_id"

    def get_organization(self):
        organization = getattr(self.request, "organization", None)
        if organization is not None:
            return organization

        membership = (
            self.request.user.organization_memberships.filter(is_active=True)
            .select_related("organization")
            .order_by("created_at")
            .first()
        )
        return membership.organization if membership else None

    def get_queryset(self):
        return super().get_queryset().for_organization(self.get_organization())

    def perform_create(self, serializer):
        serializer.save(organization=self.get_organization())
