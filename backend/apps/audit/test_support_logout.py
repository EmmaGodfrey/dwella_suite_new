from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.authtoken.models import Token

from .models import AuditEvent, SupportSession
from .support_test_utils import start

pytestmark = pytest.mark.django_db

def test_real_token_authentication_and_logout_ends_all_sessions(context):
    client, user, org, other = context
    session = start(client, org)
    second = SupportSession.objects.create(
        admin=user,
        organization=other,
        reason="Another call",
        expires_at=timezone.now() + timedelta(hours=4),
    )
    token = Token.objects.create(user=user)
    client.force_authenticate(None)
    client.credentials(
        HTTP_AUTHORIZATION=f"Token {token.key}", HTTP_X_DWELLA_WORKSPACE=str(org.public_id)
    )
    assert client.get("/api/v1/accounts/me/").status_code == 200
    client.credentials(
        HTTP_AUTHORIZATION=f"Token {token.key}", HTTP_X_DWELLA_WORKSPACE=str(other.public_id)
    )
    assert client.get("/api/v1/accounts/me/").status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}", HTTP_X_DWELLA_WORKSPACE="bad")
    assert client.get("/api/v1/accounts/me/").status_code == 403
    client.credentials(
        HTTP_AUTHORIZATION=f"Token {token.key}", HTTP_X_DWELLA_WORKSPACE=str(org.public_id)
    )
    assert client.post("/api/v1/accounts/logout/").status_code == 200
    session.refresh_from_db()
    second.refresh_from_db()
    assert session.ended_at and second.ended_at
    assert not Token.objects.filter(user=user).exists()
    assert AuditEvent.objects.filter(action="support_session.ended").count() == 2
    assert client.get("/api/v1/properties/").status_code in (401, 403)
