"""Read-only statements for the tenant identities linked to the current portal account."""

from rest_framework import generics, serializers
from rest_framework.exceptions import NotFound

from apps.documents.views import private_headers
from apps.reports.common import ReportView, organization_today
from apps.reports.serializers import PeriodParameters
from apps.reports.statements import statement_response
from apps.tenants.models import Tenant

from .views import PortalMixin


class StatementAccountSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    name = serializers.CharField(source="full_name", read_only=True)


class StatementAccountListView(PortalMixin, generics.ListAPIView):
    serializer_class = StatementAccountSerializer

    def get_queryset(self):
        portal = self.portal
        return Tenant.objects.filter(
            organization=portal.organization, pk__in=portal.tenant_ids,
        ).only("public_id", "full_name").order_by("created_at", "pk")

    def finalize_response(self, request, response, *args, **kwargs):
        return private_headers(super().finalize_response(request, response, *args, **kwargs))


class PortalStatementParameters(PeriodParameters):
    # Identity comes from the authorised path; portfolio filters do not belong in this view.
    property = None


class StatementView(PortalMixin, ReportView):
    def get(self, request, public_id):
        portal = self.portal
        tenant = next((row for row in portal.tenants if row.public_id == public_id), None)
        if tenant is None:
            raise NotFound()
        today = organization_today(portal.organization)
        parameters = PortalStatementParameters(
            data=request.query_params, context={"today": today},
        )
        parameters.is_valid(raise_exception=True)
        return statement_response(
            request, portal.organization, tenant, parameters.validated_data, today,
        )
