"""Best-effort notice intents; business writes survive outbox failures."""

import logging
import uuid

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from .models import OperationalDelivery
from .operational import enqueue

WATCH = {
    "billing.invoice": "status",
    "billing.payment": "reversed_at",
    "leases.lease": "status",
    "maintenance.maintenancerequest": "status",
}
logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=settings.AUTH_USER_MODEL, dispatch_uid="operational_deleted_recipient")
def deleted_recipient(sender, instance, **kwargs):
    # SET_NULL must not turn a previously account-bound tenant notice into an
    # accountless delivery when the account is deleted.
    OperationalDelivery.objects.filter(
        recipient_user=instance, status__in=["queued", "held", "sending"],
    ).update(status="cancelled", reason="permission_removed")


def safe_enqueue(instance, event, **kwargs):
    try:
        # Isolate database errors without poisoning the caller's business transaction.
        with transaction.atomic():
            enqueue(instance, event, **kwargs)
    except Exception:
        logger.exception("Operational notice enqueue failed: %s", event)


@receiver(pre_save, dispatch_uid="operational_previous_state")
def previous_state(sender, instance, raw=False, update_fields=None, **kwargs):
    instance.__dict__.pop("_notice_old", None)
    field = WATCH.get(sender._meta.label_lower)
    fields = [field]
    if sender._meta.label_lower == "maintenance.maintenancerequest":
        fields.append("scheduled_for")
    if raw or not field or not instance.pk or (
        update_fields is not None and not set(fields).intersection(update_fields)
    ):
        return
    instance._notice_old = sender.objects.filter(pk=instance.pk).values_list(*fields).first()


@receiver(post_save, dispatch_uid="operational_domain_event")
def domain_event(sender, instance, created, raw=False, update_fields=None, **kwargs):
    if raw:
        return
    label = sender._meta.label_lower
    field = WATCH.get(label)
    if not field and label != "maintenance.maintenanceupdate":
        return
    value = getattr(instance, field, None) if field else None
    old = instance.__dict__.pop("_notice_old", None)
    watched = {field, "scheduled_for"} if label == "maintenance.maintenancerequest" else {field}
    changed = created or (
        old is not None
        and old
        != (
            (value, instance.scheduled_for)
            if label == "maintenance.maintenancerequest"
            else (value,)
        )
        and (update_fields is None or watched.intersection(update_fields))
    )
    if label == "maintenance.maintenanceupdate":
        if created and instance.kind == "comment" and not instance.is_internal:
            safe_enqueue(instance, "repair.comment", suffix=str(instance.pk), actor=instance.author)
    elif changed:
        if label == "billing.invoice":
            if created or value == "void":
                safe_enqueue(instance, "invoice.issued" if created else "invoice.void")
        elif label == "billing.payment":
            if created or value:
                safe_enqueue(
                    instance, "payment.corrected" if value else "payment.confirmed",
                    actor=instance.reversed_by if value else instance.recorded_by,
                )
        elif label == "leases.lease":
            if value in {"pending_signature", "active", "ended"}:
                safe_enqueue(instance, f"lease.{value}", state=value)
        elif label == "maintenance.maintenancerequest":
            safe_enqueue(
                instance,
                "repair.created" if created else "repair.status",
                state=value,
                # update_fields=['scheduled_for'] does not advance updated_at.
                # Every real transition needs a new intent, even when moved back.
                suffix=str(uuid.uuid4()) if not created else "",
                actor=instance.reported_by if created else getattr(instance, "_notice_actor", None),
            )
