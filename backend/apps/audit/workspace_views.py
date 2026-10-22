from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Max, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.billing.models import Invoice
from apps.common.permissions import IsPlatformAdmin
from apps.organizations.models import Organization
from apps.organizations.serializers import OrganizationSerializer

from .workspace_actions import WorkspaceActions


class WorkspaceSerializer(OrganizationSerializer):
    properties_count = serializers.IntegerField(read_only=True)
    units_count = serializers.IntegerField(read_only=True)
    occupied_units = serializers.IntegerField(read_only=True)
    active_leases = serializers.IntegerField(read_only=True)
    outstanding_balance = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    last_activity = serializers.DateTimeField(read_only=True)
    members = serializers.SerializerMethodField()

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + [
            "properties_count", "units_count", "occupied_units", "active_leases",
            "outstanding_balance", "last_activity", "members",
        ]
        read_only_fields = fields

    def get_members(self, obj):
        return [{
            "id": str(m.public_id), "user_id": m.user_id,
            "name": m.user.get_full_name() or m.user.email or m.user.username,
            "email": m.user.email, "role": m.role, "is_active": m.is_active,
            "has_two_factor": hasattr(m.user, "two_factor_device")
            and m.user.two_factor_device.is_confirmed,
        } for m in obj.memberships.all()]


class WorkspaceFilters(serializers.Serializer):
    active = serializers.BooleanField(required=False)
    created_after = serializers.DateField(required=False)
    created_before = serializers.DateField(required=False)

    def validate(self, data):
        if data.get("created_after") and data.get("created_before") and (
            data["created_after"] > data["created_before"]
        ):
            raise ValidationError("Start date must not be after end date.")
        return data


class PlatformWorkspaceViewSet(WorkspaceActions, viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsPlatformAdmin]
    serializer_class = WorkspaceSerializer
    lookup_field = "public_id"
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    search_fields = ["name", "display_name", "email", "town", "memberships__user__email"]

    @action(detail=False, methods=["get"])
    def summary(self, request):
        counts = Organization.objects.aggregate(
            active=Count("pk", filter=Q(is_active=True)),
            suspended=Count("pk", filter=Q(is_active=False)),
            new_this_week=Count("pk", filter=Q(created_at__gte=timezone.now() - timedelta(days=7))),
        )
        counts["outstanding_balance"] = str(Invoice.objects.filter(
            status__in=Invoice.UNPAID_STATUSES,
        ).aggregate(amount=Sum(F("total") - F("amount_paid")))["amount"] or 0)
        return Response(counts)

    def get_queryset(self):
        from django.db.models import Prefetch

        from apps.organizations.models import OrganizationMembership

        amounts = Invoice.objects.filter(
            organization=OuterRef("pk"), status__in=Invoice.UNPAID_STATUSES,
        ).values("organization").annotate(balance=Sum(F("total") - F("amount_paid")))
        query = Organization.objects.annotate(
            properties_count=Count("propertys", distinct=True),
            units_count=Count("units", distinct=True),
            occupied_units=Count(
                "units", filter=Q(units__occupancy_status="occupied"), distinct=True,
            ),
            active_leases=Count("leases", filter=Q(leases__status="active"), distinct=True),
            outstanding_balance=Coalesce(
                Subquery(amounts.values("balance")[:1]), Value(Decimal("0")),
                output_field=DecimalField(max_digits=16, decimal_places=2),
            ),
            last_activity=Max("audit_events__created_at"),
        ).prefetch_related(Prefetch(
            "memberships", queryset=OrganizationMembership.objects.select_related(
                "user__two_factor_device",
            ).order_by("created_at"),
        )).order_by("-created_at", "pk")
        filters = WorkspaceFilters(data=dict(self.request.query_params.items()))
        filters.is_valid(raise_exception=True)
        for name, field in [
            ("active", "is_active"), ("created_after", "created_at__date__gte"),
            ("created_before", "created_at__date__lte"),
        ]:
            if name in filters.validated_data:
                query = query.filter(**{field: filters.validated_data[name]})
        return query
