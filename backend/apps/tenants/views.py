from decimal import Decimal

from django.db.models import F, Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.common.viewsets import OrganizationScopedModelViewSet
from apps.imports.importers import TenantImporter
from apps.imports.views import ImportActionsMixin
from apps.leases.models import Lease

from .archive import archive_tenant, restore_tenant
from .models import Tenant
from .serializers import TenantSerializer


class TenantViewSet(ImportActionsMixin, OrganizationScopedModelViewSet):
    importer_class = TenantImporter

    def get_throttles(self):
        from apps.accounts.invitations import InvitationWriteThrottle

        result = super().get_throttles()
        return (
            [*result, InvitationWriteThrottle()]
            if self.action in {"invite", "revoke_invite", "remove_portal_access"}
            else result
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        # Archived tenants leave the everyday list; ?is_active=false shows them.
        if self.action == "list" and "is_active" not in self.request.query_params:
            queryset = queryset.filter(is_active=True)
        return queryset

    @action(detail=True, methods=["post"])
    def archive(self, request, public_id=None):
        tenant = archive_tenant(request, self.get_object())
        return Response(self.get_serializer(self.get_queryset().get(pk=tenant.pk)).data)

    @action(detail=True, methods=["post"])
    def restore(self, request, public_id=None):
        tenant = restore_tenant(request, self.get_object())
        return Response(self.get_serializer(self.get_queryset().get(pk=tenant.pk)).data)

    @action(detail=True, methods=["post"])
    def invite(self, request, public_id=None):
        from apps.accounts.invitations import issue_tenant_invitation

        return Response(issue_tenant_invitation(request, self.get_object()))

    @action(detail=True, methods=["post"], url_path="revoke-invite")
    def revoke_invite(self, request, public_id=None):
        from apps.accounts.invitations import revoke_tenant_invitation

        return Response(revoke_tenant_invitation(request, self.get_object()))

    @action(detail=True, methods=["post"], url_path="remove-portal-access")
    def remove_portal_access(self, request, public_id=None):
        from apps.accounts.invitations import remove_portal_access

        return Response(remove_portal_access(request, self.get_object()))

    serializer_class = TenantSerializer
    queryset = Tenant.objects.prefetch_related(
        "portal_invitations",
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
        if (
            instance.leases.exists()
            or instance.invoices.exists()
            or instance.portal_invitations.exists()
        ):
            raise ValidationError(
                {"tenant": ["This tenant has leases or invoices, so they are kept on file."]}
            )
        instance.delete()
