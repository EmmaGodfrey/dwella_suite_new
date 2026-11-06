"""The alpha recipient exception never substitutes for number ownership."""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.access_state import mark_email_verified
from apps.organizations.models import Organization, OrganizationMembership

from .models import NotificationPhoneLink, PhoneMessagingConsent
from .test_whatsapp import BASE, callback, client
from .test_whatsapp import config as config  # noqa: F401
from .whatsapp.models import WhatsAppBinding

pytestmark = pytest.mark.django_db
PHONE = "+260972345678"


@pytest.fixture
def house():
    org = Organization.objects.create(name="External alpha")
    user = get_user_model().objects.create_user(username="alpha", email="alpha@example.com")
    mark_email_verified(user)
    OrganizationMembership.objects.create(organization=org, user=user, role="landlord")
    return {"org": org, "tenant": user}


@pytest.mark.parametrize("signature", [True, False])
def test_alpha_connection_still_requires_signed_exact_number_and_website_completion(
    house, settings, signature,
):
    settings.ALPHA_TEST_ENABLED = True
    settings.OUTBOUND_PHONE_ALLOWLIST = []
    api = client(house["tenant"])
    payload = {"channel": "whatsapp", "phone": PHONE, "actions": True, "consent": False}
    assert APIClient().post(BASE + "phone-link/", payload, format="json").status_code == 403
    response = api.post(BASE + "phone-link/", payload, format="json")
    assert response.status_code == 200
    link = response.json()["response_data"]
    complete = {"channel": "whatsapp", "complete": link["id"], "actions": True}
    assert api.post(BASE + "phone-link/", complete, format="json").status_code == 400
    message = {"id": "wamid.alpha-connect", "from": PHONE[1:],
               "timestamp": str(int(timezone.now().timestamp())),
               "type": "text", "text": {"body": link["message"]}}
    wrong = {**message, "id": "wamid.alpha-wrong", "from": "260973456789"}
    assert callback([wrong]).status_code == 200
    assert not NotificationPhoneLink.objects.get(pk=link["id"]).verified_at
    response = callback([message], valid=signature)
    assert response.status_code == (200 if signature else 403)
    challenge = NotificationPhoneLink.objects.get(pk=link["id"])
    assert bool(challenge.verified_at) == signature
    assert not WhatsAppBinding.objects.exists()
    assert api.post(BASE + "phone-link/", complete, format="json").status_code == (
        200 if signature else 400
    )
    if signature:
        assert WhatsAppBinding.objects.get().phone == PHONE
        assert not PhoneMessagingConsent.objects.get(phone=PHONE).allowed
        assert api.post(BASE + "phone-link/", complete, format="json").status_code == 400


def test_alpha_does_not_allow_changed_email_to_request_phone_link(house, settings):
    settings.ALPHA_TEST_ENABLED = True
    user = house["tenant"]
    user.email = "changed@example.com"
    user.save(update_fields=["email"])
    response = client(user).post(BASE + "phone-link/", {
        "channel": "whatsapp", "phone": PHONE, "actions": True,
    }, format="json")
    assert response.status_code == 403
    assert not NotificationPhoneLink.objects.exists()
