from contextlib import contextmanager

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import PermissionDenied

from apps.organizations.models import Organization

from .catalog import BETA_DEFAULTS, Feature, Resource
from .models import WorkspaceAccessPolicy


class AccessUnavailable(PermissionDenied):
    def __init__(self, *, feature=None, resource=None, reason, limit=None, used=None):
        detail = {
            "message": "This feature is not available for this workspace."
            if feature
            else "This workspace has reached its record limit.",
            "code": "feature_unavailable" if feature else "capacity_exceeded",
            "reason": reason,
        }
        if feature:
            detail["feature"] = feature
        if resource:
            detail.update(resource=resource, limit=limit, used=used)
        super().__init__(detail)


def _policy(organization):
    return WorkspaceAccessPolicy.objects.filter(organization=organization).first()


def feature_state(policy, feature):
    feature = Feature(feature).value
    overrides = policy.feature_overrides if policy else {}
    if not isinstance(overrides, dict):
        return {"enabled": False, "expires_at": None, "reason": "invalid_policy"}
    if feature not in overrides:
        return {"enabled": BETA_DEFAULTS[feature], "expires_at": None, "reason": None}
    rule = overrides[feature]
    if not isinstance(rule, dict) or type(rule.get("enabled")) is not bool:
        return {"enabled": False, "expires_at": None, "reason": "invalid_policy"}
    expiry = rule.get("expires_at")
    if expiry is not None:
        try:
            parsed = parse_datetime(expiry)
            if parsed is None or timezone.is_naive(parsed):
                raise ValueError("An offset is required")
        except (TypeError, ValueError):
            return {"enabled": False, "expires_at": None, "reason": "invalid_policy"}
        if parsed <= timezone.now():
            return {"enabled": False, "expires_at": expiry, "reason": "expired"}
    return {
        "enabled": rule["enabled"],
        "expires_at": expiry,
        "reason": None if rule["enabled"] else "not_included",
    }


def require_feature(organization, feature):
    if (
        not organization
        or not Organization.objects.filter(pk=organization.pk, is_active=True).exists()
    ):
        raise AccessUnavailable(feature=Feature(feature).value, reason="workspace_unavailable")
    state = feature_state(_policy(organization), feature)
    if not state["enabled"]:
        raise AccessUnavailable(feature=Feature(feature).value, reason=state["reason"])


def resource_model(resource):
    from apps.properties.models import Property, Unit
    from apps.tenants.models import Tenant

    return {Resource.PROPERTIES: Property, Resource.UNITS: Unit, Resource.TENANTS: Tenant}[
        Resource(resource)
    ]


def usage(organization, resource):
    # Stored records include archived ones. This is capacity, not a billable-unit definition.
    return resource_model(resource).objects.for_organization(organization).count()


def _limit(policy, resource):
    limits = policy.limits if policy else {}
    if not isinstance(limits, dict):
        return 0
    value = limits.get(Resource(resource).value)
    return value if value is None or (type(value) is int and value >= 0) else 0


def access_snapshot(organization):
    policy = _policy(organization)
    limits = {}
    for resource in Resource:
        used, limit = usage(organization, resource), _limit(policy, resource)
        limits[resource.value] = {
            "limit": limit,
            "used": used,
            "remaining": None if limit is None else max(0, limit - used),
        }
    return {
        "organization_id": str(organization.public_id),
        "features": {feature.value: feature_state(policy, feature) for feature in Feature},
        "limits": limits,
    }


@contextmanager
def capacity_guard(organization, resource, *, additional=1):
    """Hold the policy lock through the write; reusable for single creates/atomic imports."""
    resource = Resource(resource).value
    if type(additional) is not int or additional < 0:
        raise ValueError("additional must be a nonnegative integer")
    if (
        not organization
        or not Organization.objects.filter(pk=organization.pk, is_active=True).exists()
    ):
        raise AccessUnavailable(resource=resource, reason="workspace_unavailable")
    with transaction.atomic():
        # Match setup/reference allocation: organization first, policy second.
        current_org = Organization.objects.select_for_update().get(pk=organization.pk)
        if not current_org.is_active:
            raise AccessUnavailable(resource=resource, reason="workspace_unavailable")
        policy, _ = WorkspaceAccessPolicy.objects.select_for_update().get_or_create(
            organization=organization,
        )
        limit = _limit(policy, resource)
        before = usage(organization, resource) if limit is not None else 0
        if limit is not None and before + additional > limit:
            raise AccessUnavailable(
                resource=resource, reason="record_limit", limit=limit, used=before
            )
        yield
        if limit is not None and usage(organization, resource) > max(before, limit):
            raise AccessUnavailable(
                resource=resource, reason="record_limit", limit=limit, used=before
            )
