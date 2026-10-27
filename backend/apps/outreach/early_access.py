from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.services import record_event
from apps.marketing.emails import BetaEmailError, deliver
from apps.marketing.models import BetaApplication, BetaEmail

from .models import LIVE_ENROLLMENTS, Contact, Enrollment, OutreachSettings, Sequence, Suppression


def check_access_email(email):
    if not email:
        raise ValidationError({"email": "An email address is required for early access."})
    if Suppression.objects.filter(email__iexact=email).exists():
        raise ValidationError("This email is permanently suppressed.")


def deliver_access(application):
    check_access_email(application.email)
    if application.status == BetaApplication.Status.DECLINED:
        raise ValidationError("This beta signup was declined. Review its status first.")
    try:
        deliver(application, BetaEmail.Kind.ACCESS, resend=False)
    except BetaEmailError as error:
        raise ValidationError(str(error)) from error
    except Exception as error:
        raise ValidationError(
            "Access email could not be delivered. Check the mail connection."
        ) from error
    application.status = BetaApplication.Status.ACCEPTED
    application.save(update_fields=["status", "updated_at"])


@transaction.atomic
def give_early_access(contact, request):
    OutreachSettings.objects.get_or_create(pk=1)
    OutreachSettings.objects.select_for_update().get(pk=1)
    contact = Contact.objects.select_for_update().get(pk=contact.pk)
    check_access_email(contact.email)
    if contact.status in ("do_not_contact", "bounced", "not_interested"):
        raise ValidationError("Early access is unavailable for this contact.")
    application = BetaApplication.objects.filter(email__iexact=contact.email).order_by("pk").first()
    if application is None:
        application = BetaApplication.objects.create(
            name=contact.name,
            email=contact.email,
            phone=contact.phone,
            town=contact.town,
            units="",
            source="admin",
        )
    # Record before delivery: an audit failure must not send an unrecorded access email.
    record_event(request, "outreach.contact.early_access", contact)
    deliver_access(application)
    contact.beta_application = application
    contact.status = "interested"
    contact.save(update_fields=["beta_application", "status", "updated_at"])
    contact.enrollments.filter(status__in=LIVE_ENROLLMENTS).exclude(
        sequence__name="Early tester check-ins",
    ).update(status="cancelled", next_send_at=None)
    sequence = Sequence.objects.filter(name="Early tester check-ins", active=True).first()
    if sequence and not contact.enrollments.filter(sequence=sequence).exists():
        # The review queue remains the only place outreach sending is approved.
        # Early access queues, rather than silently approves, the tester check-ins.
        Enrollment.objects.create(
            contact=contact, sequence=sequence, next_send_at=timezone.now() + timedelta(days=3)
        )
    return contact
