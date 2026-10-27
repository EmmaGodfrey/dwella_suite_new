"""Beta applicant email sequence: welcome, countdown, and beta-day sign-in details.

Each step is recorded in BetaEmail before it is sent and removed again if delivery
fails, so the scheduler can run as often as it likes without sending twice.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.html import escape
from django.utils.http import urlsafe_base64_encode

from apps.accounts.security import frontend_reset_url
from apps.audit.runtime_settings import beta_open_date as configured_beta_date
from apps.audit.runtime_settings import runtime_settings

from .models import BetaApplication, BetaEmail

logger = logging.getLogger(__name__)
User = get_user_model()
Kind = BetaEmail.Kind

UNSUBSCRIBE_SALT = "marketing.beta.unsubscribe"
# Scheduled steps wait for the working day; the welcome goes out straight away.
SEND_FROM_HOUR = 8
# Countdown steps, days before the beta opens. Each runs until the next one is due.
COUNTDOWN = [(Kind.TWO_WEEKS, 14), (Kind.ONE_WEEK, 7), (Kind.EVE, 1)]


class BetaEmailError(Exception):
    pass


def beta_open_date(config=None):
    return configured_beta_date(config)


def countdown_windows(config=None):
    config = runtime_settings() if config is None else config
    opens = beta_open_date(config)
    starts = [
        (kind, opens - timedelta(days=days))
        for (kind, _), days in zip(COUNTDOWN, config["beta_countdown_days"], strict=True)
    ]
    ends = [start for _, start in starts[1:]] + [opens]
    return [(kind, start, end) for (kind, start), end in zip(starts, ends, strict=False)]


def due_steps(application, now=None, config=None):
    config = runtime_settings() if config is None else config
    now = timezone.localtime(now or timezone.now())
    today = now.date()
    if not application.email or application.status == BetaApplication.Status.DECLINED:
        return []
    sent = {email.kind: email for email in application.emails.all()}
    # Early access already delivered the sign-in details; the countdown would only confuse.
    if Kind.ACCESS in sent:
        return []
    working_hours = now.hour >= config["beta_send_hour"]
    changed = config.get("beta_schedule_changed_at")
    changed = datetime.fromisoformat(changed) if changed else None
    def step_time(day):
        return datetime.combine(day, time(config["beta_send_hour"]), tzinfo=now.tzinfo)

    if today >= beta_open_date(config):
        if (changed and application.created_at < changed
                and changed > step_time(beta_open_date(config))):
            return []
        return [Kind.ACCESS] if working_hours and Kind.ACCESS not in sent else []
    if Kind.WELCOME not in sent:
        if changed and application.created_at < changed:
            return []
        return [Kind.WELCOME]
    if application.unsubscribed_at or not working_hours:
        return []
    welcomed_on = timezone.localtime(sent[Kind.WELCOME].sent_at).date()
    for kind, start, end in countdown_windows(config):
        if changed and changed > step_time(start):
            continue
        # Someone welcomed on or after a step's date already has that news.
        if start <= today < end and kind not in sent and welcomed_on < start:
            return [kind]
    return []


def unsubscribe_token(application):
    return signing.dumps(application.pk, salt=UNSUBSCRIBE_SALT)


def application_from_token(token):
    try:
        pk = signing.loads(token, salt=UNSUBSCRIBE_SALT)
    except signing.BadSignature:
        return None
    return BetaApplication.objects.filter(pk=pk).first()


def unsubscribe_url(application):
    base = settings.PUBLIC_API_URL.rstrip("/")
    return f"{base}/api/v1/marketing/unsubscribe/{unsubscribe_token(application)}/"


def provision_account(application):
    """Find or create the applicant's landlord account. Never grants staff access."""
    with transaction.atomic():
        user = User.objects.filter(email__iexact=application.email).first()
        if user is None:
            first_name, _, last_name = application.name.strip().partition(" ")
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=application.email,
                        email=application.email,
                        first_name=first_name[:150],
                        last_name=last_name.strip()[:150],
                        password=None,
                    )
            except IntegrityError:
                user = User.objects.get(email__iexact=application.email)
        if not user.is_active:
            raise BetaEmailError("This applicant's account has been deactivated.")
        if application.account_id != user.pk:
            application.account = user
            application.save(update_fields=["account", "updated_at"])
    return user


@dataclass
class Message:
    subject: str
    preheader: str
    paragraphs: list
    cta_label: str = ""
    cta_url: str = ""
    checklist: tuple = ()
    footnote: str = ""
    countdown: bool = True


def build_message(application, kind, now=None):
    config = runtime_settings()
    opening = beta_open_date(config)
    opens = f"{opening:%A} {opening.day} {opening:%B}"
    offsets = dict(zip((item[0] for item in COUNTDOWN), config["beta_countdown_days"], strict=True))
    # Paragraphs are trusted HTML, so anything the applicant typed is escaped here.
    first_name = escape(application.name.strip().split(" ")[0])
    site = settings.MARKETING_SITE_URL.rstrip("/")
    sign_in = f"{settings.FRONTEND_URL.rstrip('/')}/login"

    if kind == Kind.WELCOME:
        return Message(
            subject="You're on the Dwella beta list",
            preheader=f"Beta opens {opens}. We'll email your sign-in details on opening day.",
            paragraphs=[
                f"Hi {first_name}, thanks for signing up for the Dwella beta.",
                f"The beta opens on <strong>{opens}</strong>. On opening day we'll email you "
                "everything you need to sign in. There's nothing else to do until then.",
                "Dwella keeps your rent, tenants and repairs in one place, and it's free "
                "for the whole beta. In the beta you can:",
            ],
            checklist=(
                "Record rent payments and print numbered receipts",
                "See who owes what with rent roll and arrears reports",
                "Keep track of leases, repairs and contractors",
            ),
            cta_label="See what's coming",
            cta_url=site,
        )
    if kind == Kind.TWO_WEEKS:
        return Message(
            subject=("Two weeks until the Dwella beta" if offsets[kind] == 14
                     else f"{offsets[kind]} days until the Dwella beta"),
            preheader="A head start: what to have ready for day one.",
            paragraphs=[
                f"Hi {first_name}, the Dwella beta opens on {opens}.",
                "Setting up takes about ten minutes when the details are to hand. "
                "If you'd like a head start, gather these:",
            ],
            checklist=(
                "Each property's name and address, and its units",
                "Your tenants' names and phone numbers",
                "Monthly rent for each unit and the day it's due",
                "When each current lease started",
            ),
        )
    if kind == Kind.ONE_WEEK:
        return Message(
            subject=("One week to go: your first ten minutes on Dwella" if offsets[kind] == 7
                     else f"{offsets[kind]} days to go: your first ten minutes on Dwella"),
            preheader="What happens after you sign in.",
            paragraphs=[
                f"Hi {first_name}, the beta opens on {opens}. "
                "Here's what your first ten minutes will look like:",
            ],
            checklist=(
                "Sign in and name your workspace",
                "Add your first property and its units",
                "Follow the setup checklist to add tenants and leases",
                "Generate your first rent invoices",
            ),
            footnote="Questions before then? Just reply to this email.",
        )
    if kind == Kind.EVE:
        return Message(
            subject=("The Dwella beta opens tomorrow" if offsets[kind] == 1
                     else f"The Dwella beta opens in {offsets[kind]} days"),
            preheader="Watch your inbox for sign-in details on opening day.",
            paragraphs=[
                f"Hi {first_name}, the beta opens on {opens}.",
                "On opening day we'll send your sign-in details to "
                f"<strong>{escape(application.email)}</strong>. If you don't see them, "
                "check your spam or promotions folder.",
            ],
        )

    user = application.account
    early = timezone.localdate(now or timezone.now()) < opening
    if user.has_usable_password():
        return Message(
            subject="You're in early" if early else "The Dwella beta is open",
            preheader="Sign in with your existing Dwella account.",
            paragraphs=[
                f"Hi {first_name}, you have early access to Dwella."
                if early
                else f"Hi {first_name}, the Dwella beta is open.",
                f"You already have an account. Sign in with <strong>{escape(user.email)}</strong> "
                "and your existing password.",
            ],
            cta_label="Sign in to Dwella",
            cta_url=sign_in,
            footnote="Forgot your password? Use Forgot password on the sign-in page.",
            countdown=False,
        )
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    days = max(1, settings.PASSWORD_RESET_TIMEOUT // 86400)
    if early:
        return Message(
            subject="You're in early: your Dwella account is ready",
            preheader=f"Early access ahead of the {opens} beta. Set your password and sign in.",
            paragraphs=[
                f"Hi {first_name}, you're one of the first people to use Dwella, ahead of "
                f"the beta opening on <strong>{opens}</strong>.",
                f"Your username is your email address: <strong>{escape(user.email)}</strong>. "
                "Choose a password to sign in:",
                "Anything confusing, broken or missing? Reply to this email and tell us. "
                "Early feedback shapes what we fix before the beta opens.",
            ],
            cta_label="Set your password",
            cta_url=f"{frontend_reset_url(uid, token)}&welcome=1",
            footnote=(
                f"This link works for {days} days and only once. After that, use Forgot "
                f"password at {sign_in} with this email address."
            ),
            countdown=False,
        )
    return Message(
        subject="Your Dwella beta account is ready",
        preheader="Set your password and sign in.",
        paragraphs=[
            f"Hi {first_name}, the Dwella beta is open and your account is ready.",
            f"Your username is your email address: <strong>{escape(user.email)}</strong>. "
            "Choose a password to sign in:",
        ],
        cta_label="Set your password",
        cta_url=f"{frontend_reset_url(uid, token)}&welcome=1",
        footnote=(
            f"This link works for {days} days and only once. After that, use Forgot "
            f"password at {sign_in} with this email address."
        ),
        countdown=False,
    )


def send_message(application, message):
    context = {
        "message": message,
        "site_url": settings.MARKETING_SITE_URL.rstrip("/"),
        "unsubscribe_url": unsubscribe_url(application) if message.countdown else "",
    }
    headers = {}
    if message.countdown:
        headers["List-Unsubscribe"] = f"<{context['unsubscribe_url']}>"
        headers["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    email = EmailMultiAlternatives(
        subject=message.subject,
        body=render_to_string("marketing/beta_email.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[application.email],
        reply_to=[settings.BETA_EMAIL_REPLY_TO] if settings.BETA_EMAIL_REPLY_TO else None,
        headers=headers,
    )
    email.attach_alternative(render_to_string("marketing/beta_email.html", context), "text/html")
    email.send(fail_silently=False)


def deliver(application, kind, *, resend=False, now=None, scheduled=False):
    """Send one step. Returns False if it was already sent and resend is off."""
    config = runtime_settings()
    if not config["beta_emails_enabled"]:
        raise BetaEmailError("Beta emails are paused in platform settings.")
    if scheduled and kind not in due_steps(application, now, config):
        return False
    if not application.email:
        raise BetaEmailError("This applicant has no email address.")
    try:
        with transaction.atomic():
            record, created = BetaEmail.objects.get_or_create(
                application=application, kind=kind, defaults={"sent_at": timezone.now()}
            )
    except IntegrityError:
        return False
    if not created and not resend:
        return False
    try:
        if kind == Kind.ACCESS:
            provision_account(application)
        send_message(application, build_message(application, kind, now))
    except Exception:
        if created:
            record.delete()
        raise
    if not created:
        record.sent_at = timezone.now()
        record.save(update_fields=["sent_at"])
    return True


def send_due_emails(applications=None, now=None):
    """Send whatever is due. Returns (sent, failed) counts."""
    config = runtime_settings()
    if not config["beta_emails_enabled"]:
        return 0, 0
    if applications is None:
        applications = (
            BetaApplication.objects.exclude(email="")
            .exclude(status=BetaApplication.Status.DECLINED)
            .prefetch_related("emails")
            .select_related("account")
        )
    sent = failed = 0
    for application in applications:
        for kind in due_steps(application, now, config):
            try:
                sent += deliver(application, kind, now=now, scheduled=True)
            except Exception:
                failed += 1
                logger.exception("Beta email %s to application %s failed", kind, application.pk)
    return sent, failed
