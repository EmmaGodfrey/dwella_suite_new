from apps.common.viewsets import OrganizationScopedModelViewSet

from .models import Property, PropertyOwner, Unit
from .serializers import PropertyOwnerSerializer, PropertySerializer, UnitSerializer


class PropertyOwnerViewSet(OrganizationScopedModelViewSet):
    serializer_class = PropertyOwnerSerializer
    queryset = PropertyOwner.objects.all()
    search_fields = ["full_name", "email", "phone_number"]
    ordering_fields = ["full_name", "created_at"]


class PropertyViewSet(OrganizationScopedModelViewSet):
    serializer_class = PropertySerializer
    queryset = Property.objects.select_related("owner")
    filterset_fields = ["property_type", "management_status", "town", "is_active"]
    search_fields = ["name", "address", "town", "province"]
    ordering_fields = ["name", "created_at", "management_status"]


class UnitViewSet(OrganizationScopedModelViewSet):
    serializer_class = UnitSerializer
    queryset = Unit.objects.select_related("property")
    filterset_fields = ["property", "occupancy_status", "is_active"]
    search_fields = ["name", "property__name"]
    ordering_fields = ["name", "rent_amount", "created_at"]
