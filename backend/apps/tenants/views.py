from decimal import Decimal

from django.db.models import Exists, F, OuterRef, Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.common.property_scope import EVERYTHING
from apps.common.viewsets import OrganizationScopedModelViewSet
from apps.imports.importers import TenantImporter
from apps.imports.views import ImportActionsMixin
from apps.leases.models import Lease

from .archive import archive_tenant, restore_tenant
from .models import Tenant
from .serializers import TenantSerializer


def tenant_queryset(scope):
    """Tenants with the leases and balance the scope may see.

    A tenant can rent in more than one property; a manager sees the person,
    but only the leases and money owed for their own properties.
    """
    return Tenant.objects.prefetch_related(
        "portal_invitations",
        Prefetch(
            "leases",
            queryset=Lease.objects.filter(scope.q("unit__property_id")).select_related(
                "unit__property"
            ),
        ),
    ).annotate(
        # What the tenant still owes across unpaid invoices.
        balance=Coalesce(
            Sum(
                F("invoices__total") - F("invoices__amount_paid"),
                filter=Q(invoices__status__in=["open", "partially_paid"])
                & scope.q("invoices__unit__property_id"),
            ),
            Decimal("0"),
        )
    )


class TenantViewSet(ImportActionsMixin, OrganizationScopedModelViewSet):
    importer_class = TenantImporter
    whole_tenant_actions = frozenset(
        {"archive", "restore", "remove_portal_access", "destroy"}
    )

    def get_object(self):
        tenant = super().get_object()
        scope = self.get_property_scope()
        # These change the tenant for every property they rent in.
        if (
            self.action in self.whole_tenant_actions
            and not scope.everything
            and tenant.leases.exclude(scope.q("unit__property_id")).exists()
        ):
            raise PermissionDenied(
                "This tenant also rents a property you do not manage. Ask a property admin."
            )
        return tenant

    def perform_create(self, serializer):
        instance = serializer.save(
            organization=self.get_organization(), created_by=self.request.user
        )
        self.check_saved(instance)

    def get_throttles(self):
        from apps.accounts.invitations import InvitationWriteThrottle

        result = super().get_throttles()
        return (
            [*result, InvitationWriteThrottle()]
            if self.action in {"invite", "revoke_invite", "remove_portal_access"}
            else result
        )

    def get_queryset(self):
        scope = self.get_property_scope()
        self.queryset = tenant_queryset(scope)
        queryset = super().get_queryset()
        # Archived tenants leave the everyday list; ?is_active=false shows them.
        if self.action == "list" and "is_active" not in self.request.query_params:
            queryset = queryset.filter(is_active=True)
        if self.action == "list" and "property" in self.request.query_params:
            try:
                property_id = serializers.UUIDField().run_validation(
                    self.request.query_params["property"],
                )
            except ValidationError as error:
                raise ValidationError({"property": error.detail}) from error
            # Lease history keeps former tenants discoverable for statements. EXISTS
            # avoids duplicate tenants and multiplying the annotated invoice balance.
            queryset = queryset.filter(Exists(Lease.objects.filter(
                scope.q("unit__property_id"),
                tenant_id=OuterRef("pk"), organization_id=OuterRef("organization_id"),
                unit__property__public_id=property_id,
                unit__property__organization_id=OuterRef("organization_id"),
            )))
        if self.action == "list" and self.request.query_params.get("details") == "missing":
            queryset = queryset.filter(
                Q(tpin="")
                | Q(billing_address="")
                | (Q(tenant_type="individual") & (Q(national_id="") | Q(identity_country="")))
                | (
                    Q(tenant_type="company")
                    & (
                        Q(company_registration="")
                        | Q(representative_name="")
                        | Q(representative_phone="")
                    )
                )
            )
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
    queryset = tenant_queryset(EVERYTHING)
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
