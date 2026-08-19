from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import IsOrganizationMember

from .models import Organization, OrganizationMembership
from .serializers import OrganizationMembershipSerializer, OrganizationSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    lookup_field = "public_id"
    lookup_url_kwarg = "public_id"

    def get_queryset(self):
        return Organization.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True,
        ).distinct()

    def perform_create(self, serializer):
        organization = serializer.save()
        OrganizationMembership.objects.create(
            organization=organization,
            user=self.request.user,
            role=OrganizationMembership.Role.OWNER,
        )


class OrganizationMembershipViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrganizationMembershipSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"
    lookup_url_kwarg = "public_id"

    def get_queryset(self):
        return (
            OrganizationMembership.objects.filter(user=self.request.user)
            .select_related("organization", "user")
            .order_by("organization__name")
        )
