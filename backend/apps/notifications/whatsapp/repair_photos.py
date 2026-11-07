"""Photos belong to a repair draft until its explicit, transactional confirmation."""

from datetime import timedelta

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.maintenance.models import MaintenancePhoto
from apps.maintenance.serializers import MAX_PHOTOS

from .media import keep
from .models import WhatsAppMedia


def add(ctx, conversation, payload):
    files = conversation.draft.setdefault("files", [])
    if len(files) >= MAX_PHOTOS:
        return f"A repair can have up to {MAX_PHOTOS} photos."
    if WhatsAppMedia.objects.filter(pk__in=files, media_id=payload["media_id"]).exists():
        return "That photo has already been added."
    files.append(keep(ctx.binding, payload["media_id"], repair=True).pk)
    return "Photo received. It will be checked before the repair is submitted."


def summary(ctx, conversation, note=""):
    from .conversation import choice, response

    draft = conversation.draft
    count = len(draft.get("files", []))
    return response(
        f'{note}\nReport repair: {draft["title"]}\n{draft["description"]}\n'
        f'Permission to enter: {"Yes" if draft["permission_to_enter"] else "No"}\n'
        f'Photos: {count}. Send photos here before confirming, or confirm without photos.',
        [
            choice(conversation, "Confirm repair", "repair_confirm", member=ctx.membership),
            *(
                [
                    choice(
                        conversation, "Remove photos", "repair_remove_photos", member=ctx.membership
                    )
                ]
                if count
                else []
            ),
            choice(conversation, "Cancel", "menu", member=ctx.membership),
        ],
    )


def ready(ctx, conversation):
    ids = conversation.draft.get("files", [])
    rows = list(
        WhatsAppMedia.objects.select_for_update()
        .filter(
            pk__in=ids,
            binding=ctx.binding,
            binding_generation=ctx.binding.generation,
        )
        .defer("content")
        .order_by("pk")
    )
    if len(rows) != len(ids) or len(rows) > MAX_PHOTOS:
        raise PermissionDenied("The repair photos changed. Start again.")
    if any(row.created_at < timezone.now() - timedelta(days=2) for row in rows):
        raise ValidationError("These photos expired. Remove them and send fresh copies.")
    if any(row.status == "rejected" for row in rows):
        raise ValidationError("One or more photos were rejected. Remove them and try again.")
    if any(row.status != "ready" for row in rows):
        raise ValidationError("The photos are still being checked. Confirm again shortly.")
    if any(
        not row.name.startswith("maintenance/photos/") or row.content_type != "image/jpeg"
        for row in rows
    ):
        raise PermissionDenied("These files do not belong to a repair.")
    return rows


def attach(job, user, rows):
    # Files were validated and stored by the media worker without locks. Assigning
    # an existing file name inserts references only: no storage I/O here.
    MaintenancePhoto.objects.bulk_create(
        [MaintenancePhoto(request=job, uploaded_by=user, image=row.name) for row in rows]
    )
    WhatsAppMedia.objects.filter(pk__in=[row.pk for row in rows]).delete()


def wanted(row, conversation):
    from .access import actor_context
    from .conversation import _repair_lease

    if conversation.expires_at <= timezone.now() or conversation.draft.get("intent") != "repair":
        return False
    try:
        ctx = actor_context(row.binding, conversation.organization_id)
        if ctx.role != "tenant":
            return False
        _repair_lease(ctx, conversation.draft["lease"])
    except (PermissionDenied, KeyError):
        return False
    return True
