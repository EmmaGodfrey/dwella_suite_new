from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Invoice
from apps.common.permissions import get_active_membership
from apps.common.workspaces import resolve_workspace
from apps.leases.models import Lease
from apps.properties.models import Property, Unit
from apps.subscriptions.catalog import Resource
from apps.subscriptions.services import capacity_guard
from apps.tenants.models import Tenant

from .models import Organization, OrganizationMembership


class SetupSerializer(serializers.Serializer):
    business_name = serializers.CharField(max_length=180)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone_number = serializers.RegexField(
        r"^\+?[\d\s-]{7,40}$", required=False, allow_blank=True, default=""
    )
    property_name = serializers.CharField(max_length=180)
    property_type = serializers.ChoiceField(choices=Property.PropertyType.choices)
    address = serializers.CharField(max_length=1000)
    town = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    unit_name = serializers.CharField(max_length=80)
    rent_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))


def setup_status(user, request=None):
    membership = get_active_membership(user)
    org = (
        resolve_workspace(request) if request else (membership.organization if membership else None)
    )
    editable = (
        bool(org)
        if user.is_staff or user.is_superuser
        else (not membership or membership.role == OrganizationMembership.Role.LANDLORD)
    )
    models = [Property, Unit, Tenant, Lease, Invoice]
    counts = [model.objects.for_organization(org).count() if org else 0 for model in models]
    active_leases = (
        Lease.objects.for_organization(org).filter(status="active").count() if org else 0
    )
    return {
        "needs_setup": editable and not counts[0],
        "can_setup": editable,
        "business_name": str(org) if org else "",
        "email": org.email if org else user.email,
        "phone_number": org.phone_number if org else "",
        "steps": [
            {
                "key": "workspace",
                "label": "Set up your workspace",
                "done": bool(org),
                "path": "/setup",
            },
            {
                "key": "property",
                "label": "Add your first property and unit",
                "done": bool(counts[0] and counts[1]),
                "path": "/properties",
            },
            {
                "key": "tenant",
                "label": "Add your first tenant",
                "done": bool(counts[2]),
                "path": "/tenants",
            },
            {
                "key": "lease",
                "label": "Activate a lease",
                "done": bool(active_leases),
                "path": "/leases",
            },
            {
                "key": "invoice",
                "label": "Generate your first rent invoice",
                "done": bool(counts[4]),
                "path": "/billing",
            },
        ],
    }


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def check_access(self, request):
        resolve_workspace(request)
        membership = get_active_membership(request.user)
        from apps.accounts.models import AccountAccessState

        if (
            not membership
            and not (request.user.is_staff or request.user.is_superuser)
            and AccountAccessState.objects.filter(
                user=request.user, tenant_access_removed=True
            ).exists()
        ):
            raise PermissionDenied(
                "Tenant access was removed. Ask your property manager for a new invitation."
            )
        if (
            membership
            and membership.role == "tenant"
            and not (request.user.is_staff or request.user.is_superuser)
        ):
            raise PermissionDenied("Setup is for landlords.")
        return membership

    def get(self, request):
        self.check_access(request)
        return Response(setup_status(request.user, request))

    @transaction.atomic
    def post(self, request):
        # Serialize repeat submissions and prevent two workspaces for a new account.
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        self.check_access(request)
        if not setup_status(request.user, request)["can_setup"]:
            raise PermissionDenied("Only a landlord can complete setup.")
        serializer = SetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        resolved = resolve_workspace(request)
        if resolved:
            org = Organization.objects.select_for_update().get(pk=resolved.pk)
            if Property.objects.for_organization(org).exists():
                raise ValidationError(
                    {
                        "property_name": [
                            "Setup is already complete. Add properties from Properties."
                        ]
                    }
                )
            org.display_name = data["business_name"]
            org.email = data["email"]
            org.phone_number = data["phone_number"]
            org.save(update_fields=["display_name", "email", "phone_number", "updated_at"])
        else:
            # A unique internal name allows two businesses to share a display name.
            org = Organization.objects.create(
                name=f"workspace-{uuid4().hex}",
                display_name=data["business_name"],
                email=data["email"],
                phone_number=data["phone_number"],
            )
            OrganizationMembership.objects.create(
                organization=org, user=request.user, role=OrganizationMembership.Role.LANDLORD
            )
            request.organization = org
            request._request.organization = org
        with capacity_guard(org, Resource.PROPERTIES), capacity_guard(org, Resource.UNITS):
            property_obj = Property.objects.create(
                organization=org,
                name=data["property_name"],
                property_type=data["property_type"],
                address=data["address"],
                town=data["town"],
            )
            Unit.objects.create(
                organization=org,
                property=property_obj,
                name=data["unit_name"],
                rent_amount=data["rent_amount"],
            )
        return Response(setup_status(request.user, request), status=201)
