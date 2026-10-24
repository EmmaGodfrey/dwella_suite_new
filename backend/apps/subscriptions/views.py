from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.common.permissions import CanViewPortfolio, IsPlatformSuperuser
from apps.common.workspaces import resolve_workspace
from apps.organizations.models import Organization

from .models import WorkspaceAccessPolicy
from .serializers import AccessPolicyPatchSerializer
from .services import access_snapshot


class PolicyWriteThrottle(UserRateThrottle):
    scope = "access_policy_write"
    rate = "30/hour"


class PrivateAccessView(APIView):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


class WorkspaceEntitlementsView(PrivateAccessView):
    permission_classes = [IsAuthenticated, CanViewPortfolio]
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        return Response(access_snapshot(resolve_workspace(request)))


class PlatformEntitlementsView(PrivateAccessView):
    permission_classes = [IsPlatformSuperuser]
    http_method_names = ["get", "patch", "head", "options"]

    def get_throttles(self):
        throttles = super().get_throttles()
        return [*throttles, PolicyWriteThrottle()] if self.request.method == "PATCH" else throttles

    def get(self, request, public_id):
        organization = get_object_or_404(Organization, public_id=public_id)
        return Response(access_snapshot(organization))

    @transaction.atomic
    def patch(self, request, public_id):
        organization = get_object_or_404(
            Organization.objects.select_for_update(), public_id=public_id
        )
        serializer = AccessPolicyPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        policy, _ = WorkspaceAccessPolicy.objects.select_for_update().get_or_create(
            organization=organization,
        )
        before = {"feature_overrides": policy.feature_overrides, "limits": policy.limits}
        features, limits = dict(policy.feature_overrides), dict(policy.limits)
        for key, rule in serializer.validated_data.get("feature_overrides", {}).items():
            if rule is None:
                features.pop(key, None)
            else:
                features[key] = rule
        limits.update(serializer.validated_data.get("limits", {}))
        policy.feature_overrides, policy.limits = features, limits
        policy.save(update_fields=["feature_overrides", "limits", "updated_at"])
        record_event(
            request,
            "subscription.access_policy_updated",
            policy,
            organization,
            before=before,
            after={"feature_overrides": features, "limits": limits},
        )
        return Response(access_snapshot(organization))
