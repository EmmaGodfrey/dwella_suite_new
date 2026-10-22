from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from rest_framework.test import APIClient

from .emails import due_steps, send_due_emails, unsubscribe_token
from .models import BetaApplication, BetaEmail

URL = "/api/v1/marketing/beta-applications/"
ADMIN_URL = "/api/v1/marketing/admin/beta-applications/"
LUSAKA = ZoneInfo("Africa/Lusaka")
User = get_user_model()
Kind = BetaEmail.Kind


def at(day, hour=9):
    return datetime(2026, 11, day, hour, tzinfo=LUSAKA)


def oct_(day, hour=9):
    return datetime(2026, 10, day, hour, tzinfo=LUSAKA)


@pytest.fixture(autouse=True)
def beta_settings(settings):
    cache.clear()
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.BETA_EMAILS_ENABLED = True
    settings.BETA_OPEN_DATE = "2026-11-18"
    settings.FRONTEND_URL = "https://app.dwella.properties"
    settings.PUBLIC_API_URL = "https://api.dwella.properties"
    return settings


def applicant(**overrides):
    data = {
        "name": "Bwalya Mulenga",
        "phone": "097 123 4567",
        "email": "bwalya@example.com",
        "role": "Landlord",
        "units": "6-20",
    }
    data.update(overrides)
    return BetaApplication.objects.create(**data)


def welcomed(application, when):
    BetaEmail.objects.create(application=application, kind=Kind.WELCOME, sent_at=when)
    return application


def admin_client():
    admin = User.objects.create_superuser(
        username="admin@example.com", email="admin@example.com", password="StrongerPass123"
    )
    client = APIClient()
    client.force_authenticate(admin)
    return client


@pytest.mark.django_db(transaction=True)
def test_website_signup_sends_a_welcome_email_once():
    data = {
        "name": "Bwalya Mulenga",
        "phone": "097 123 4567",
        "email": "Bwalya@Example.com",
        "role": "Landlord",
        "units": "6-20",
    }
    with mock.patch("django.utils.timezone.now", return_value=oct_(22)):
        assert APIClient().post(URL, data, format="json").status_code == 201
        repeat = APIClient().post(URL, data, format="json")

    assert repeat.status_code == 201
    assert BetaApplication.objects.count() == 1
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["bwalya@example.com"]
    assert message.subject == "You're on the Dwella beta list"
    assert "Wednesday 18 November" in message.body
    assert "List-Unsubscribe" in message.extra_headers
    assert BetaEmail.objects.filter(kind=Kind.WELCOME).count() == 1


@pytest.mark.django_db(transaction=True)
def test_signup_succeeds_when_email_delivery_fails():
    data = {
        "name": "Bwalya",
        "phone": "097 123 4567",
        "email": "b@example.com",
        "role": "Landlord",
        "units": "1-5",
    }
    with mock.patch("apps.marketing.emails.send_message", side_effect=OSError("smtp down")):
        response = APIClient().post(URL, data, format="json")

    assert response.status_code == 201
    # Nothing recorded, so the scheduler retries the welcome later.
    assert not BetaEmail.objects.exists()


@pytest.mark.django_db
def test_nothing_is_sent_or_recorded_while_emails_are_disabled(settings):
    settings.BETA_EMAILS_ENABLED = False
    applicant()
    assert send_due_emails(now=oct_(22)) == (0, 0)
    assert not mail.outbox and not BetaEmail.objects.exists()


@pytest.mark.django_db
def test_countdown_steps_follow_the_calendar():
    application = welcomed(applicant(), oct_(22))

    assert due_steps(application, oct_(30)) == []
    assert due_steps(application, at(4)) == [Kind.TWO_WEEKS]
    # Late runs still deliver the current step but never a superseded one.
    assert due_steps(application, at(9)) == [Kind.TWO_WEEKS]
    assert due_steps(application, at(11)) == [Kind.ONE_WEEK]
    assert due_steps(application, at(17)) == [Kind.EVE]
    assert due_steps(application, at(4, hour=6)) == []


@pytest.mark.django_db
def test_late_signups_skip_steps_their_welcome_already_covered():
    application = welcomed(applicant(), at(12))
    assert due_steps(application, at(12, 15)) == []
    assert due_steps(application, at(17)) == [Kind.EVE]


@pytest.mark.django_db
def test_declined_unsubscribed_and_emailless_applicants_are_skipped(settings):
    declined = welcomed(applicant(email="d@example.com", status="declined"), oct_(22))
    quiet = welcomed(applicant(email="q@example.com", unsubscribed_at=oct_(23)), oct_(22))
    no_email = applicant(email="")

    assert due_steps(declined, at(4)) == []
    assert due_steps(quiet, at(4)) == []
    assert due_steps(no_email, oct_(22)) == []
    assert due_steps(declined, at(18)) == []
    # Unsubscribing stops the countdown, not the sign-in details.
    assert due_steps(quiet, at(18)) == [Kind.ACCESS]


@pytest.mark.django_db
def test_beta_day_creates_a_landlord_account_and_emails_a_set_password_link():
    application = welcomed(applicant(name="Bwalya Mulenga Phiri"), oct_(22))

    with mock.patch("django.utils.timezone.now", return_value=at(18)):
        call_command("send_beta_emails")
        call_command("send_beta_emails")

    application.refresh_from_db()
    user = application.account
    assert user.email == "bwalya@example.com" and user.username == "bwalya@example.com"
    assert (user.first_name, user.last_name) == ("Bwalya", "Mulenga Phiri")
    assert not user.is_staff and not user.is_superuser
    assert not user.has_usable_password()
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.subject == "Your Dwella beta account is ready"
    assert "List-Unsubscribe" not in message.extra_headers
    link = next(word for word in message.body.split() if "reset_token=" in word)
    assert link.startswith("https://app.dwella.properties/login?reset_uid=")
    assert link.endswith("&welcome=1")
    token = link.split("reset_token=")[1].split("&")[0]
    assert default_token_generator.check_token(user, token)


@pytest.mark.django_db
def test_existing_accounts_are_linked_without_touching_their_password():
    existing = User.objects.create_user(
        username="landlord", email="bwalya@example.com", password="StrongerPass123"
    )
    application = welcomed(applicant(email="BWALYA@example.com"), oct_(22))

    send_due_emails(now=at(18))

    application.refresh_from_db()
    existing.refresh_from_db()
    assert application.account == existing
    assert existing.check_password("StrongerPass123")
    assert User.objects.count() == 1
    assert mail.outbox[0].subject == "The Dwella beta is open"
    assert "reset_token" not in mail.outbox[0].body


@pytest.mark.django_db
def test_failed_delivery_is_retried_on_the_next_run():
    welcomed(applicant(), oct_(22))
    with mock.patch("apps.marketing.emails.send_message", side_effect=OSError("smtp down")):
        assert send_due_emails(now=at(4)) == (0, 1)
    assert send_due_emails(now=at(4)) == (1, 0)
    assert mail.outbox[0].subject == "Two weeks until the Dwella beta"


@pytest.mark.django_db
def test_applicant_names_are_escaped_in_html():
    applicant(name="<script>alert(1)</script> Mulenga")
    send_due_emails(now=oct_(22))
    html = mail.outbox[0].alternatives[0][0]
    assert "<script>" not in html and "&lt;script&gt;" in html


@pytest.mark.django_db
def test_admin_can_sign_someone_up_and_send_the_welcome():
    client = admin_client()
    with mock.patch("django.utils.timezone.now", return_value=oct_(22)):
        with mock.patch("django.db.transaction.on_commit", side_effect=lambda fn: fn()):
            response = client.post(
                ADMIN_URL,
                {
                    "name": "Chanda Banda",
                    "phone": "+260 97 765 4321",
                    "email": "chanda@example.com",
                    "role": "Agent",
                    "units": "21-50",
                    "town": "Ndola",
                },
                format="json",
            )

    assert response.status_code == 201
    data = response.json()["response_data"]
    assert data["source"] == "admin"
    assert BetaApplication.objects.get().source == BetaApplication.Source.ADMIN
    assert mail.outbox[0].to == ["chanda@example.com"]


@pytest.mark.django_db
def test_admin_signup_requires_a_unique_valid_email_and_staff_access():
    applicant(email="taken@example.com")
    payload = {"name": "Chanda Banda", "phone": "0977654321", "role": "Agent", "units": "1-5"}

    assert APIClient().post(ADMIN_URL, payload, format="json").status_code == 403
    landlord = User.objects.create_user(username="l", password="StrongerPass123")
    client = APIClient()
    client.force_authenticate(landlord)
    assert client.post(ADMIN_URL, payload, format="json").status_code == 403

    client = admin_client()
    missing = client.post(ADMIN_URL, payload, format="json")
    assert missing.status_code == 400
    taken = client.post(ADMIN_URL, {**payload, "email": "Taken@example.com"}, format="json")
    assert taken.status_code == 400
    disposable = client.post(ADMIN_URL, {**payload, "email": "x@mailinator.com"}, format="json")
    assert disposable.status_code == 400
    assert BetaApplication.objects.count() == 1


@pytest.mark.django_db
def test_admin_signup_can_skip_the_welcome():
    client = admin_client()
    with mock.patch("django.db.transaction.on_commit", side_effect=lambda fn: fn()):
        response = client.post(
            ADMIN_URL,
            {
                "name": "Chanda Banda",
                "phone": "0977654321",
                "email": "c@example.com",
                "role": "Agent",
                "units": "1-5",
                "send_welcome": False,
            },
            format="json",
        )
    assert response.status_code == 201
    assert not mail.outbox


@pytest.mark.django_db
def test_admin_can_send_access_early_and_resend_a_fresh_link():
    application = applicant()
    client = admin_client()
    url = f"{ADMIN_URL}{application.pk}/send-access/"

    first = client.post(url)
    second = client.post(url)

    assert first.status_code == 200 and second.status_code == 200
    assert second.json()["response_data"]["status"] == "accepted"
    assert second.json()["response_data"]["account_email"] == "bwalya@example.com"
    assert len(mail.outbox) == 2
    assert BetaEmail.objects.filter(kind=Kind.ACCESS).count() == 1
    assert User.objects.filter(email="bwalya@example.com").count() == 1


@pytest.mark.django_db
def test_send_access_refuses_declined_emailless_and_disabled(settings):
    client = admin_client()
    declined = applicant(email="d@example.com", status="declined")
    no_email = applicant(email="")
    assert client.post(f"{ADMIN_URL}{declined.pk}/send-access/").status_code == 400
    assert client.post(f"{ADMIN_URL}{no_email.pk}/send-access/").status_code == 400
    settings.BETA_EMAILS_ENABLED = False
    ok = applicant(email="ok@example.com")
    assert client.post(f"{ADMIN_URL}{ok.pk}/send-access/").status_code == 400
    assert not mail.outbox and not User.objects.filter(email="ok@example.com").exists()


@pytest.mark.django_db
def test_send_access_does_not_reactivate_a_disabled_account():
    User.objects.create_user(username="x", email="bwalya@example.com", is_active=False)
    application = applicant()
    response = admin_client().post(f"{ADMIN_URL}{application.pk}/send-access/")
    assert response.status_code == 400
    assert not BetaEmail.objects.filter(kind=Kind.ACCESS).exists()


@pytest.mark.django_db
def test_admin_cannot_change_email_once_the_account_exists():
    client = admin_client()
    application = applicant()
    client.post(f"{ADMIN_URL}{application.pk}/send-access/")
    response = client.patch(
        f"{ADMIN_URL}{application.pk}/", {"email": "new@example.com"}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_unsubscribe_confirms_on_get_and_applies_on_post():
    application = applicant()
    url = f"/api/v1/marketing/unsubscribe/{unsubscribe_token(application)}/"
    client = APIClient(enforce_csrf_checks=True)

    page = client.get(url)
    application.refresh_from_db()
    assert page.status_code == 200 and application.unsubscribed_at is None

    assert client.post(url).status_code == 200
    application.refresh_from_db()
    assert application.unsubscribed_at is not None


@pytest.mark.django_db
def test_unsubscribe_rejects_tampered_tokens():
    application = applicant()
    token = unsubscribe_token(application)
    response = APIClient().post(f"/api/v1/marketing/unsubscribe/{token[:-2]}xx/")
    assert response.status_code == 404
    application.refresh_from_db()
    assert application.unsubscribed_at is None
