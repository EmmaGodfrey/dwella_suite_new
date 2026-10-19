from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.common.viewsets import OrganizationScopedModelViewSet

from .models import Lease
from .serializers import LeaseSerializer
from .services import activate_lease, end_lease


class LeaseFilter(filters.FilterSet):
    tenant = filters.UUIDFilter(field_name="tenant__public_id")
    unit = filters.UUIDFilter(field_name="unit__public_id")
    property = filters.UUIDFilter(field_name="unit__property__public_id")

    class Meta:
        model = Lease
        fields = ["tenant", "unit", "property", "status"]


class LeaseViewSet(OrganizationScopedModelViewSet):
    serializer_class = LeaseSerializer
    queryset = Lease.objects.select_related("tenant", "unit__property")
    filterset_class = LeaseFilter
    search_fields = ["reference", "tenant__full_name", "unit__name", "unit__property__name"]
    ordering_fields = ["start_date", "end_date", "created_at", "reference"]

    @action(detail=True, methods=["post"])
    def activate(self, request, public_id=None):
        lease = activate_lease(self.get_object())
        return Response(self.get_serializer(lease).data)

    @action(detail=True, methods=["post"])
    def end(self, request, public_id=None):
        lease = end_lease(self.get_object())
        return Response(self.get_serializer(lease).data)

    def perform_destroy(self, instance):
        if instance.status != Lease.Status.DRAFT:
            raise ValidationError({"lease": ["Only a draft lease can be deleted. End it instead."]})
        instance.delete()
