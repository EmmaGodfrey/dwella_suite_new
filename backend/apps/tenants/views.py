from django.db.models import Prefetch
from rest_framework.exceptions import ValidationError

from apps.common.viewsets import OrganizationScopedModelViewSet
from apps.leases.models import Lease

from .models import Tenant
from .serializers import TenantSerializer


class TenantViewSet(OrganizationScopedModelViewSet):
    serializer_class = TenantSerializer
    queryset = Tenant.objects.prefetch_related(
        Prefetch("leases", queryset=Lease.objects.select_related("unit__property"))
    )
    filterset_fields = ["status", "is_active"]
    search_fields = ["full_name", "phone_number", "email", "national_id"]
    ordering_fields = ["full_name", "created_at", "status"]
    ordering = ["full_name"]

    def perform_destroy(self, instance):
        # Leases and (soon) payments hang off a tenant; deleting them would
        # erase the rent history, so a tenant with a lease is kept on file.
        if instance.leases.exists():
            raise ValidationError({"tenant": ["This tenant has leases, so they are kept on file."]})
        instance.delete()
