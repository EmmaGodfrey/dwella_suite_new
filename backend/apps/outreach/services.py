import json
from datetime import timedelta
from email.utils import make_msgid
from hashlib import sha256

from django.core import signing
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import (
    LIVE_ENROLLMENTS,
    Contact,
    Enrollment,
    OutreachMessage,
    OutreachSettings,
    Suppression,
)
from .rendering import render_template


def ensure_contact_allowed(contact):
    if contact.status in ("do_not_contact", "bounced", "not_interested") or (
        contact.email and Suppression.objects.filter(email__iexact=contact.email).exists()
    ):
        raise ValidationError("This contact is suppressed or does not want further outreach.")
    if contact.replied_at:
        raise ValidationError("This contact has replied. Automated follow-ups are stopped.")
    if not contact.email:
        raise ValidationError({"email": "An email address is required."})


@transaction.atomic
def change_contact_status(contact, status):
    contact = Contact.objects.select_for_update().get(pk=contact.pk)
    if contact.status in ("do_not_contact", "bounced") and status != contact.status:
        raise ValidationError("Suppression history cannot be cleared.")
    contact.status = status
    if status in ("do_not_contact", "bounced"):
        if contact.email:
            Suppression.objects.get_or_create(
                email=contact.email.lower(),
                defaults={"reason": "bounced" if status == "bounced" else "manual"},
            )
        stop = "stopped_bounce" if status == "bounced" else "stopped_optout"
    elif status in ("replied", "interested", "partner", "not_interested"):
        contact.replied_at = timezone.now()
        stop = "stopped_reply"
    else:
        if contact.status in ("do_not_contact", "bounced") or contact.replied_at:
            raise ValidationError("Reply and suppression history cannot be cleared.")
        stop = None
    contact.save()
    if stop:
        contact.enrollments.filter(status__in=LIVE_ENROLLMENTS).update(
            status=stop,
            next_send_at=None,
        )
    return contact


def preview_enrollment(enrollment):
    config, _ = OutreachSettings.objects.get_or_create(pk=1)
    steps = list(enrollment.sequence.steps.select_related("template").all())
    if not enrollment.sequence.active or not steps or any(not s.template.active for s in steps):
        raise ValidationError("This sequence has no active steps.")
    return [
        {
            **render_template(step.template, enrollment.contact, config, enrollment.personal_line),
            "step": step.order,
            "wait_days": step.wait_days,
        }
        for step in steps
    ]


def review_snapshot(enrollment):
    ensure_contact_allowed(enrollment.contact)
    messages = preview_enrollment(enrollment)
    digest = sha256(
        json.dumps(
            {"email": enrollment.contact.email, "messages": messages}, sort_keys=True
        ).encode()
    ).hexdigest()
    token = signing.dumps(
        {"enrollment": str(enrollment.public_id), "digest": digest}, salt="outreach.review.v1"
    )
    return {"messages": messages, "preview_token": token, "digest": digest}


@transaction.atomic
def approve_enrollment(enrollment, user, preview_token):
    contact = Contact.objects.select_for_update().get(pk=enrollment.contact_id)
    enrollment = (
        Enrollment.objects.select_for_update()
        .select_related("sequence", "contact")
        .get(
            pk=enrollment.pk,
        )
    )
    ensure_contact_allowed(contact)
    if enrollment.status != "pending_review":
        raise ValidationError("Only a pending review can be approved.")
    snapshot = review_snapshot(enrollment)
    try:
        checked = signing.loads(preview_token, salt="outreach.review.v1", max_age=600)
    except (signing.BadSignature, TypeError) as error:
        raise ValidationError("Preview this email again before approving.") from error
    if checked != {"enrollment": str(enrollment.public_id), "digest": snapshot["digest"]}:
        raise ValidationError("The message changed. Preview it again before approving.")
    copies = snapshot["messages"]
    for copy in copies:
        OutreachMessage.objects.create(
            enrollment=enrollment,
            recipient=contact.email,
            message_id=make_msgid(domain="dwella"),
            **copy,
        )
    enrollment.approved_by = user
    enrollment.approved_at = timezone.now()
    enrollment.status = "scheduled"
    enrollment.next_send_at = max(
        timezone.now(),
        enrollment.created_at + timedelta(days=copies[0]["wait_days"]),
    )
    enrollment.save()
    return enrollment
