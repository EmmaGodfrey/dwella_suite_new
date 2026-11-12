"""Which properties the signed-in person may work on.

Property admins and audited platform support see the whole workspace. A
property manager sees the properties assigned to them, plus a teammate's while
an open cover session lasts. Everything else is denied by default: a model with
no registered path to a property is hidden from property managers.
"""

from dataclasses import dataclass

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

# Lookups from each record to the property it belongs to. A record reachable
# through more than one path is visible when any path lands in scope.
PATHS = {
    "properties.property": ("pk",),
    "properties.unit": ("property_id",),
    "leases.lease": ("unit__property_id",),
    "billing.invoice": ("unit__property_id",),
    "billing.payment": ("invoice__unit__property_id",),
    "billing.depositdeduction": ("lease__unit__property_id",),
    "billing.depositentry": ("lease__unit__property_id",),
    "billing.depositevidence": ("deduction__lease__unit__property_id",),
    "billing.paymentproof": ("invoice__unit__property_id",),
    "billing.paymentprooffile": ("proof__invoice__unit__property_id",),
    "maintenance.maintenancerequest": ("property_id",),
    "documents.documentversion": ("invoice__unit__property_id", "lease__unit__property_id"),
    "documents.signedleaseoriginal": ("lease__unit__property_id",),
    "integrations.fiscalreceipt": ("invoice__unit__property_id",),
    "payments.collection": ("invoice__unit__property_id",),
    "notifications.messagedelivery": ("invoice__unit__property_id",),
}

# Records the whole management team shares; they belong to no single property.
SHARED = {"maintenance.vendor", "billing.paymentinstruction"}

ADMIN_ONLY = "Only a property admin can do this."
OUT_OF_SCOPE = "This property is not assigned to you."


@dataclass(frozen=True)
class PropertyScope:
    everything: bool = False
    own_ids: frozenset = frozenset()
    cover_ids: frozenset = frozenset()
    cover: object = None
    user_id: int | None = None

    @property
    def ids(self):
        return self.own_ids | self.cover_ids

    def allows(self, property_id):
        return self.everything or (property_id is not None and property_id in self.ids)

    def q(self, *paths):
        """A filter matching records whose property is in scope."""
        if self.everything:
            return Q()
        ids = self.ids
        if not ids:
            return Q(pk__in=[])
        condition = Q()
        for path in paths:
            condition |= Q(**{f"{path}__in": ids})
        return condition

    def filter(self, queryset):
        if self.everything:
            return queryset
        label = queryset.model._meta.label_lower
        if label == "tenants.tenant":
            return queryset.filter(self.tenant_q())
        if label in SHARED:
            return queryset
        paths = PATHS.get(label)
        if paths is None:
            raise ImproperlyConfigured(f"{label} has no property scope path.")
        return queryset.filter(self.q(*paths))

    def tenant_q(self):
        """Tenants with a lease, past or present, in an in-scope property.

        A tenant no lease has placed yet stays visible to the manager who
        added them, so they can finish the lease.
        """
        from apps.leases.models import Lease

        leases = Lease.objects.filter(tenant_id=OuterRef("pk"))
        unplaced = Q(created_by_id=self.user_id) & ~Exists(leases)
        if not self.ids:
            return unplaced
        return Exists(leases.filter(unit__property_id__in=self.ids)) | unplaced


EVERYTHING = PropertyScope(everything=True)
NOTHING = PropertyScope()


def active_cover(membership):
    from apps.organizations.models import CoverSession

    return (
        CoverSession.objects.filter(
            manager=membership, ended_at__isnull=True, expires_at__gt=timezone.now()
        )
        .select_related("covering_for__user")
        .first()
    )


def scope_for_membership(membership):
    from apps.organizations.models import OrganizationMembership, PropertyAssignment

    if not membership or not membership.is_active:
        return NOTHING
    if membership.role == OrganizationMembership.Role.LANDLORD:
        return EVERYTHING
    if membership.role != OrganizationMembership.Role.MANAGER:
        return NOTHING
    cover = active_cover(membership) if membership.organization.allow_teammate_cover else None
    mine = Q(membership=membership)
    if cover:
        # The teammate's assignments are read live, so the cover shrinks as
        # soon as an admin changes or removes the teammate.
        mine |= Q(
            membership_id=cover.covering_for_id,
            membership__is_active=True,
            membership__role=OrganizationMembership.Role.MANAGER,
        )
    own, covered = set(), set()
    rows = PropertyAssignment.objects.filter(
        mine,
        organization_id=membership.organization_id,
        property__organization_id=membership.organization_id,
    ).values_list("property_id", "membership_id")
    for property_id, membership_id in rows:
        (own if membership_id == membership.pk else covered).add(property_id)
    covered -= own
    return PropertyScope(
        own_ids=frozenset(own),
        cover_ids=frozenset(covered),
        cover=cover if covered else None,
        user_id=membership.user_id,
    )


def _raw(request):
    return getattr(request, "_request", request)


def property_scope(request):
    """The request's scope, read once per request."""
    raw = _raw(request)
    cached = getattr(raw, "_property_scope", None)
    user = request.user
    if cached is not None and cached[0] == user.pk:
        return cached[1]
    if not user or not user.is_authenticated:
        scope = NOTHING
    elif user.is_staff or user.is_superuser:
        # Platform staff reach a workspace only through an audited support
        # session, which resolve_workspace enforces separately.
        scope = EVERYTHING
    else:
        from .permissions import get_active_membership
        from .workspaces import resolve_workspace

        resolve_workspace(request)
        resolved = getattr(request, "_workspace_membership", None)
        membership = (
            resolved[1] if resolved and resolved[0] == user.pk else get_active_membership(user)
        )
        scope = scope_for_membership(membership)
    raw._property_scope = (user.pk if user else None, scope)
    return scope


def is_property_admin(request):
    return property_scope(request).everything


def require_property_admin(request, message=ADMIN_ONLY):
    if not is_property_admin(request):
        raise PermissionDenied(message)


def scoped(request, queryset):
    """A workspace queryset narrowed to the request's workspace and properties."""
    from .workspaces import resolve_workspace

    return property_scope(request).filter(queryset.for_organization(resolve_workspace(request)))


def scoped_for_view(view, model):
    """What a serializer may offer for a related field: the workspace and scope of its view."""
    if view is None:
        return model.objects.none()
    return property_scope(view.request).filter(
        model.objects.for_organization(view.get_organization())
    )


def property_ids_of(obj):
    """The properties a record belongs to, following its registered paths."""
    found = set()
    for path in PATHS.get(obj._meta.label_lower, ()):
        value = obj
        for part in path.split("__"):
            value = getattr(value, part, None)
            if value is None:
                break
        if value is not None:
            found.add(value)
    return found


def touch(request, *property_ids):
    """Remember which properties a write reached, for the cover audit trail."""
    raw = _raw(request)
    touched = getattr(raw, "_property_touches", None)
    if touched is None:
        touched = raw._property_touches = set()
    touched.update(pid for pid in property_ids if pid is not None)


def require_in_scope(request, obj, message=OUT_OF_SCOPE):
    """Refuse a record outside the request's properties; note the ones it reached."""
    scope = property_scope(request)
    ids = property_ids_of(obj)
    if obj._meta.label_lower in SHARED:
        return obj
    if not scope.everything:
        if obj._meta.label_lower == "tenants.tenant":
            if not type(obj).objects.filter(scope.tenant_q(), pk=obj.pk).exists():
                raise PermissionDenied(message)
            if scope.cover:
                # A tenant belongs to the properties their leases are in.
                ids = set(
                    obj.leases.filter(unit__property_id__in=scope.ids).values_list(
                        "unit__property_id", flat=True
                    )
                )
        elif not ids or not all(scope.allows(pid) for pid in ids):
            raise PermissionDenied(message)
    touch(request, *ids)
    return obj


def scoped_object(request, queryset, **lookup):
    """Fetch one in-scope record or 404, noting the property a write reached."""
    obj = get_object_or_404(scoped(request, queryset), **lookup)
    touch(request, *property_ids_of(obj))
    return obj


def cover_event_details(request):
    """Audit details when a successful write reached a covered property."""
    raw = _raw(request)
    cached = getattr(raw, "_property_scope", None)
    scope = cached[1] if cached else None
    if not scope or not scope.cover:
        return None
    reached = getattr(raw, "_property_touches", set()) & scope.cover_ids
    if not reached:
        return None
    teammate = scope.cover.covering_for.user
    return {
        "cover_session": str(scope.cover.public_id),
        "on_behalf_of": teammate.pk,
        "on_behalf_of_name": teammate.get_full_name().strip() or teammate.email,
        "reason": scope.cover.reason,
        "property_ids": sorted(reached),
    }
