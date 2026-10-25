from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.common.references import next_reference
from apps.properties.models import Unit
from apps.tenants.models import Tenant

from .models import Lease

UNIT_TAKEN_MESSAGE = "This unit already has an open lease."
# Terms a renewal copies from the lease it follows; the manager may change them.
RENEWAL_TERMS = (
    "monthly_rent",
    "deposit_amount",
    "rent_due_day",
    "late_fee_percent",
    "late_fee_grace_days",
    "notice_period_months",
    "notes",
)


def conflicting_leases(unit, lease=None):
    """Open leases that stop `unit` taking `lease` (or a new lease).

    A lease and its renewal hold the same unit one after the other, so they do
    not conflict with each other.
    """
    query = Lease.objects.filter(unit=unit, status__in=Lease.OPEN_STATUSES)
    if lease is not None and lease.pk:
        query = query.exclude(pk=lease.pk).exclude(renewal_of=lease)
        if lease.renewal_of_id:
            query = query.exclude(pk=lease.renewal_of_id)
    return query


def next_lease_reference(organization):
    """Return the next `LSE-0001` style reference. Call inside a transaction."""
    return next_reference(organization, Lease, "LSE")


def create_lease(*, organization, activate=False, **fields):
    try:
        with transaction.atomic():
            # Serialise new leases per unit; the serializer's check ran unlocked.
            Unit.objects.select_for_update().filter(pk=fields["unit"].pk).first()
            if conflicting_leases(fields["unit"]).exists():
                raise ValidationError({"unit": [UNIT_TAKEN_MESSAGE]})
            lease = Lease.objects.create(
                organization=organization,
                reference=next_lease_reference(organization),
                **fields,
            )
            if activate:
                lease = activate_lease(lease)
    except IntegrityError as error:
        # The serializer checks for an open lease first; this catches the race
        # where another request took the unit in between.
        raise ValidationError({"unit": [UNIT_TAKEN_MESSAGE]}) from error
    return lease


@transaction.atomic
def create_renewal(lease, *, end_date, **terms):
    """Copy `lease` into a draft that starts the day after it ends.

    Starting exactly the next day keeps rent billing to one lease per month
    and leaves no unbilled gap. The tenant signs the renewal like any lease.
    """
    lease = Lease.objects.select_for_update().select_related("unit", "tenant").get(pk=lease.pk)
    if lease.status != Lease.Status.ACTIVE:
        raise ValidationError({"status": ["Only an active lease can be renewed."]})
    if lease.renewals.filter(status__in=Lease.OPEN_STATUSES).exists():
        raise ValidationError({"lease": ["This lease already has a renewal in progress."]})
    if not lease.tenant.is_active:
        raise ValidationError({"tenant": ["This tenant is archived."]})
    start = lease.end_date + timedelta(days=1)
    if end_date <= start:
        raise ValidationError({"end_date": ["The renewal must end after it starts."]})
    fields = {name: terms.get(name, getattr(lease, name)) for name in RENEWAL_TERMS}
    try:
        with transaction.atomic():
            return Lease.objects.create(
                organization=lease.organization,
                reference=next_lease_reference(lease.organization),
                tenant=lease.tenant,
                unit=lease.unit,
                start_date=start,
                end_date=end_date,
                renewal_of=lease,
                **fields,
            )
    except IntegrityError as error:
        message = "This lease already has a renewal in progress."
        raise ValidationError({"lease": [message]}) from error


@transaction.atomic
def activate_lease(lease):
    lease = Lease.objects.select_for_update().get(pk=lease.pk)
    if lease.status not in (Lease.Status.DRAFT, Lease.Status.PENDING_SIGNATURE):
        raise ValidationError({"status": ["Only a draft or unsigned lease can be activated."]})
    if lease.renewal_of_id:
        if lease.start_date > timezone.localdate():
            raise ValidationError(
                {"status": [f"This renewal starts on {lease.start_date:%d %B %Y}."]}
            )
        previous = Lease.objects.select_for_update().get(pk=lease.renewal_of_id)
        if previous.status == Lease.Status.ACTIVE:
            # Its term is over; the renewal takes over the unit without a vacancy.
            previous.status = Lease.Status.ENDED
            previous.ended_at = timezone.now()
            previous.save(update_fields=["status", "ended_at", "updated_at"])
    lease.status = Lease.Status.ACTIVE
    lease.activated_at = timezone.now()
    lease.save(update_fields=["status", "activated_at", "updated_at"])
    Unit.objects.filter(pk=lease.unit_id).update(occupancy_status=Unit.OccupancyStatus.OCCUPIED)
    Tenant.objects.filter(pk=lease.tenant_id).update(status=Tenant.Status.ACTIVE)
    return lease


@transaction.atomic
def end_lease(lease):
    if lease.status != Lease.Status.ACTIVE:
        raise ValidationError({"status": ["Only an active lease can be ended."]})
    lease.status = Lease.Status.ENDED
    lease.ended_at = timezone.now()
    lease.save(update_fields=["status", "ended_at", "updated_at"])
    Unit.objects.filter(pk=lease.unit_id).update(occupancy_status=Unit.OccupancyStatus.VACANT)
    still_renting = Lease.objects.filter(
        tenant_id=lease.tenant_id, status=Lease.Status.ACTIVE
    ).exists()
    if not still_renting:
        Tenant.objects.filter(pk=lease.tenant_id).update(status=Tenant.Status.PAST)
    return lease


def start_due_renewals(today=None):
    """Activate signed renewals whose start date has arrived.

    Only a renewal with a fully signed Dwella version or a retained signed
    original starts automatically; an unsigned one waits for the manager.
    Returns the leases that were started.
    """
    from apps.documents.models import DocumentVersion, SignedLeaseOriginal

    today = today or timezone.localdate()
    due = Lease.objects.filter(
        renewal_of__isnull=False,
        is_active=True,
        status__in=(Lease.Status.DRAFT, Lease.Status.PENDING_SIGNATURE),
        start_date__lte=today,
        organization__is_active=True,
    )
    signed = due.filter(
        pk__in=DocumentVersion.objects.filter(status="signed").values("lease_id")
    ) | due.filter(pk__in=SignedLeaseOriginal.objects.values("lease_id"))
    started = []
    for lease in signed.distinct().order_by("start_date", "pk"):
        try:
            started.append(activate_lease(lease))
        except ValidationError:
            continue  # Changed meanwhile; the manager can still start it by hand.
    return started
