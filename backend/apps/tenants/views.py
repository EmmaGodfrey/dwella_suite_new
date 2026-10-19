from decimal import Decimal

from django.db.models import F, Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError

from apps.common.viewsets import OrganizationScopedModelViewSet
from apps.leases.models import Lease

from .models import Tenant
from .serializers import TenantSerializer


class TenantViewSet(OrganizationScopedModelViewSet):
    serializer_class = TenantSerializer
    queryset = Tenant.objects.prefetch_related(
        Prefetch("leases", queryset=Lease.objects.select_related("unit__property"))
    ).annotate(
        # What the tenant still owes across unpaid invoices.
        balance=Coalesce(
            Sum(
                F("invoices__total") - F("invoices__amount_paid"),
                filter=Q(invoices__status__in=["open", "partially_paid"]),
            ),
            Decimal("0"),
        )
    )
    filterset_fields = ["status", "is_active"]
    search_fields = ["full_name", "phone_number", "email", "national_id"]
    ordering_fields = ["full_name", "created_at", "status"]
    ordering = ["full_name"]

    def perform_destroy(self, instance):
        # Leases and (soon) payments hang off a tenant; deleting them would
        # erase the rent history, so a tenant with a lease is kept on file.
        if instance.leases.exists() or instance.invoices.exists():
            raise ValidationError(
                {"tenant": ["This tenant has leases or invoices, so they are kept on file."]}
            )
        instance.delete()
