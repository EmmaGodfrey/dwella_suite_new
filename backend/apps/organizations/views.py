from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated

from apps.common.permissions import CanManageOrganization, IsOrganizationMember

from .models import Organization, OrganizationMembership
from .serializers import OrganizationMembershipSerializer, OrganizationSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    lookup_field = "public_id"
    lookup_url_kwarg = "public_id"

    def get_permissions(self):
        permissions = [IsAuthenticated, IsOrganizationMember]
        if self.request.method not in SAFE_METHODS:
            permissions.append(CanManageOrganization)
        return [permission() for permission in permissions]

    def get_queryset(self):
        queryset = Organization.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True,
        ).distinct()
        if self.request.method not in SAFE_METHODS:
            queryset = queryset.filter(
                memberships__user=self.request.user,
                memberships__is_active=True,
                memberships__role__in=[
                    OrganizationMembership.Role.OWNER,
                    OrganizationMembership.Role.ADMIN,
                ],
            )
        return queryset

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
