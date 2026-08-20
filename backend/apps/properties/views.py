from decimal import Decimal

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsOrganizationMember
from apps.common.viewsets import OrganizationScopedModelViewSet

from .models import Property, PropertyOwner, Unit
from .serializers import PropertyOwnerSerializer, PropertySerializer, UnitSerializer


def decimal_to_float(value):
    return float(value or Decimal("0"))


def percentage(part, whole):
    if not whole:
        return 0
    return round((part / whole) * 100, 1)


class PropertyDashboardSummaryView(APIView):
    permission_classes = [IsOrganizationMember]

    def get_organization(self):
        membership = (
            self.request.user.organization_memberships.filter(is_active=True)
            .select_related("organization")
            .order_by("created_at")
            .first()
        )
        return membership.organization if membership else None

    def get(self, request):
        organization = self.get_organization()
        if organization is None:
            return Response(
                {
                    "organization": None,
                    "properties": {
                        "total": 0,
                        "active": 0,
                        "managed": 0,
                        "prospect": 0,
                        "archived": 0,
                        "by_status": [],
                        "by_type": [],
                    },
                    "units": {
                        "total": 0,
                        "occupied": 0,
                        "vacant": 0,
                        "maintenance": 0,
                        "reserved": 0,
                        "occupancy_rate": 0,
                    },
                    "finance": {
                        "monthly_rent_roll": 0,
                        "occupied_rent_roll": 0,
                        "vacancy_loss": 0,
                        "average_unit_rent": 0,
                    },
                    "portfolio": {
                        "towns_count": 0,
                        "average_units_per_property": 0,
                    },
                    "recent_properties": [],
                    "top_units": [],
                }
            )

        properties = Property.objects.for_organization(organization)
        units = Unit.objects.for_organization(organization).select_related("property")

        property_totals = properties.aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(is_active=True)),
        )
        property_total = property_totals["total"]

        rent_totals = units.aggregate(
            total_units=Count("id"),
            monthly_rent_roll=Coalesce(Sum("rent_amount"), Decimal("0")),
            occupied_rent_roll=Coalesce(
                Sum("rent_amount", filter=Q(occupancy_status=Unit.OccupancyStatus.OCCUPIED)),
                Decimal("0"),
            ),
            average_unit_rent=Coalesce(Avg("rent_amount"), Decimal("0")),
        )
        unit_total = rent_totals["total_units"]

        property_status_counts = {
            item["management_status"]: item["total"]
            for item in properties.values("management_status").annotate(total=Count("id"))
        }
        property_type_counts = {
            item["property_type"]: item["total"]
            for item in properties.values("property_type").annotate(total=Count("id"))
        }
        unit_status_counts = {
            item["occupancy_status"]: item["total"]
            for item in units.values("occupancy_status").annotate(total=Count("id"))
        }
        occupied_units = unit_status_counts.get(Unit.OccupancyStatus.OCCUPIED, 0)
        vacant_units = unit_status_counts.get(Unit.OccupancyStatus.VACANT, 0)
        maintenance_units = unit_status_counts.get(Unit.OccupancyStatus.MAINTENANCE, 0)
        reserved_units = unit_status_counts.get(Unit.OccupancyStatus.RESERVED, 0)

        recent_properties = [
            {
                "id": str(property_obj.public_id),
                "name": property_obj.name,
                "property_type": property_obj.property_type,
                "management_status": property_obj.management_status,
                "town": property_obj.town,
                "address": property_obj.address,
                "units_count": property_obj.units_count,
            }
            for property_obj in properties.annotate(units_count=Count("units"))
            .order_by("-created_at")[:5]
        ]

        top_units = [
            {
                "id": str(unit.public_id),
                "name": unit.name,
                "property_name": unit.property.name,
                "occupancy_status": unit.occupancy_status,
                "rent_amount": decimal_to_float(unit.rent_amount),
            }
            for unit in units.order_by("-rent_amount")[:5]
        ]

        return Response(
            {
                "organization": {
                    "id": str(organization.public_id),
                    "name": organization.name,
                    "display_name": organization.display_name,
                },
                "properties": {
                    "total": property_total,
                    "active": property_totals["active"],
                    "managed": property_status_counts.get(Property.ManagementStatus.MANAGED, 0),
                    "prospect": property_status_counts.get(Property.ManagementStatus.PROSPECT, 0),
                    "archived": property_status_counts.get(Property.ManagementStatus.ARCHIVED, 0),
                    "by_status": [
                        {
                            "key": key,
                            "label": label,
                            "count": property_status_counts.get(key, 0),
                        }
                        for key, label in Property.ManagementStatus.choices
                    ],
                    "by_type": [
                        {
                            "key": key,
                            "label": label,
                            "count": property_type_counts.get(key, 0),
                        }
                        for key, label in Property.PropertyType.choices
                    ],
                },
                "units": {
                    "total": unit_total,
                    "occupied": occupied_units,
                    "vacant": vacant_units,
                    "maintenance": maintenance_units,
                    "reserved": reserved_units,
                    "occupancy_rate": percentage(occupied_units, unit_total),
                    "by_status": [
                        {
                            "key": key,
                            "label": label,
                            "count": unit_status_counts.get(key, 0),
                            "percentage": percentage(unit_status_counts.get(key, 0), unit_total),
                        }
                        for key, label in Unit.OccupancyStatus.choices
                    ],
                },
                "finance": {
                    "monthly_rent_roll": decimal_to_float(rent_totals["monthly_rent_roll"]),
                    "occupied_rent_roll": decimal_to_float(rent_totals["occupied_rent_roll"]),
                    "vacancy_loss": decimal_to_float(
                        rent_totals["monthly_rent_roll"] - rent_totals["occupied_rent_roll"]
                    ),
                    "average_unit_rent": decimal_to_float(rent_totals["average_unit_rent"]),
                },
                "portfolio": {
                    "towns_count": properties.exclude(town="").values("town").distinct().count(),
                    "average_units_per_property": round(unit_total / property_total, 1)
                    if property_total
                    else 0,
                },
                "recent_properties": recent_properties,
                "top_units": top_units,
            }
        )


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
