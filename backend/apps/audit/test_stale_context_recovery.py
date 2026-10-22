from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.authtoken.models import Token

from .models import AuditEvent, SupportSession
from .support_test_utils import URL, start

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("state", ["expired", "ended", "malformed", "unknown", "blank"])
def test_stale_context_allows_recovery_but_never_portfolio_access(context, state):
    client, user, org, other = context
    session = start(client, org)
    if state == "expired":
        session.expires_at = timezone.now() - timedelta(seconds=1)
    elif state == "ended":
        session.ended_at = timezone.now()
    session.save()
    header = {"malformed": "bad", "unknown": str(other.public_id), "blank": ""}.get(
        state, str(org.public_id)
    )
    token = Token.objects.create(user=user)
    client.force_authenticate(None)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}", HTTP_X_DWELLA_WORKSPACE=header)
    me = client.get("/api/v1/accounts/me/")
    assert me.status_code == 200
    assert me.json()["response_data"]["access"]["acting_workspace"] is None
    assert client.get("/api/v1/properties/").status_code == 403
    assert client.get("/api/v1/properties/dashboard/").status_code == 403
    assert client.get(URL + "?active=true").status_code == 200
    created = client.post(
        URL, {"organization": str(org.public_id), "reason": "Recover support access"},
        format="json",
    )
    assert created.status_code == 201
    assert client.post(f"{URL}{session.public_id}/end/").status_code == 200
    assert client.post("/api/v1/accounts/logout/").status_code == 200
    assert not Token.objects.filter(user=user).exists()
    assert not SupportSession.objects.filter(admin=user, ended_at__isnull=True).exists()
    assert AuditEvent.objects.filter(action="support_session.started").count() == 2
    assert client.get(URL).status_code == 403


def test_recovery_still_requires_authentication_and_staff(context):
    client, user, org, _ = context
    client.force_authenticate(None)
    client.credentials(HTTP_X_DWELLA_WORKSPACE="bad")
    assert client.get("/api/v1/accounts/me/").status_code == 403
    assert client.post("/api/v1/accounts/logout/").status_code == 403
    assert client.post(URL, {}, format="json").status_code == 403
    user.is_staff = False
    user.save(update_fields=["is_staff"])
    client.credentials(
        HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}",
        HTTP_X_DWELLA_WORKSPACE=str(org.public_id),
    )
    assert client.post(URL, {}, format="json").status_code == 403
