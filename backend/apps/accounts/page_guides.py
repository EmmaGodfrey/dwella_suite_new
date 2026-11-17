"""First-visit page guides. Content is in the frontend; the server records who saw which."""

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.workspaces import resolve_workspace
from apps.organizations.models import Organization, OrganizationMembership

from .email_verification import NoStoreAccountView
from .models import GuidedTourState

# Append only. Seen state is keyed by these ids, so never rename one.
MODULES = {
    "landlord": [
        "dashboard",
        "setup",
        "properties",
        "tenants",
        "leases",
        "billing",
        "maintenance",
        "reports",
        "team",
        "settings",
        "messages",
    ],
    "tenant": ["dashboard", "billing", "leases", "maintenance", "profile", "security"],
}
PREFIX = "page:"


def _role(user, org):
    if not user.is_active or user.is_staff or user.is_superuser or not org:
        return None
    membership = OrganizationMembership.objects.filter(
        user=user, organization=org, organization__is_active=True, is_active=True
    ).first()
    return membership.role if membership else None


class PageGuideSerializer(serializers.Serializer):
    module = serializers.CharField(max_length=32)
    action = serializers.ChoiceField(choices=["seen"])


class PageGuidesView(NoStoreAccountView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = resolve_workspace(request)
        role = _role(request.user, org)
        if role not in MODULES:
            return Response({"available": False, "modules": [], "seen": []})
        seen = GuidedTourState.objects.filter(
            user=request.user, organization=org, tour_key__startswith=PREFIX
        ).values_list("tour_key", flat=True)
        return Response(
            {
                "available": True,
                "modules": MODULES[role],
                "seen": [key[len(PREFIX) :] for key in seen],
            }
        )

    @transaction.atomic
    def post(self, request):
        org = resolve_workspace(request)
        role = _role(request.user, org)
        if role not in MODULES:
            raise PermissionDenied("Page guides are not available for this account.")
        data = PageGuideSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        module = data.validated_data["module"]
        if module not in MODULES[role]:
            raise serializers.ValidationError({"module": "Unknown page."})
        if not Organization.objects.filter(pk=org.pk, is_active=True).exists():
            raise PermissionDenied("A current workspace is required.")
        GuidedTourState.objects.update_or_create(
            user=request.user,
            organization=org,
            tour_key=f"{PREFIX}{module}",
            defaults={"status": "completed"},
        )
        return self.get(request)
