from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.services import record_event
from apps.leases.models import Lease

from .models import Tenant


@transaction.atomic
def archive_tenant(request, tenant):
    """Hide a tenant from day-to-day lists while keeping every record.

    Leases, invoices, payments, documents and repairs stay as they are. A tenant
    with a lease still open (draft, awaiting signature or active) is refused;
    end or delete that lease first. Archiving also closes the tenant portal.
    """
    tenant = Tenant.objects.select_for_update().get(pk=tenant.pk)
    if not tenant.is_active:
        raise ValidationError("This tenant is already archived.")
    if tenant.leases.filter(status__in=Lease.OPEN_STATUSES).exists():
        raise ValidationError(
            {"tenant": ["End this tenant's open lease before archiving them."]}
        )
    tenant.portal_invitations.filter(accepted_at__isnull=True, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
    tenant.is_active = False
    tenant.save(update_fields=["is_active", "updated_at"])
    record_event(request, "tenant.archived", tenant, tenant.organization)
    return tenant


@transaction.atomic
def restore_tenant(request, tenant):
    tenant = Tenant.objects.select_for_update().get(pk=tenant.pk)
    if tenant.is_active:
        raise ValidationError("This tenant is not archived.")
    tenant.is_active = True
    tenant.save(update_fields=["is_active", "updated_at"])
    record_event(request, "tenant.restored", tenant, tenant.organization)
    return tenant
