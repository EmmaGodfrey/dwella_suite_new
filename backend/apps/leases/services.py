from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.common.references import next_reference
from apps.properties.models import Unit
from apps.tenants.models import Tenant

from .models import Lease

UNIT_TAKEN_MESSAGE = "This unit already has an open lease."


def next_lease_reference(organization):
    """Return the next `LSE-0001` style reference. Call inside a transaction."""
    return next_reference(organization, Lease, "LSE")


def create_lease(*, organization, activate=False, **fields):
    try:
        with transaction.atomic():
            lease = Lease.objects.create(
                organization=organization,
                reference=next_lease_reference(organization),
                **fields,
            )
            if activate:
                activate_lease(lease)
    except IntegrityError as error:
        # The serializer checks for an open lease first; this catches the race
        # where another request took the unit in between.
        raise ValidationError({"unit": [UNIT_TAKEN_MESSAGE]}) from error
    return lease


@transaction.atomic
def activate_lease(lease):
    if lease.status not in (Lease.Status.DRAFT, Lease.Status.PENDING_SIGNATURE):
        raise ValidationError({"status": ["Only a draft or unsigned lease can be activated."]})
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
