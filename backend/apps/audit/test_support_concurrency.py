from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from django.db import close_old_connections, connection, transaction
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.properties.models import Property

from .middleware import RequestAuditContextMiddleware
from .models import AuditEvent, SupportSession
from .support_test_utils import start

pytestmark = pytest.mark.django_db(transaction=True)
postgres_only = pytest.mark.skipif(connection.vendor != "postgresql", reason="Needs real row locks")


@pytest.mark.parametrize("method,path", [
    ("get", "/api/v1/properties/"),
    ("post", "/api/v1/platform/support-sessions/"),
    ("post", "/api/v1/marketing/beta-applications/"),
])
def test_reads_and_unrelated_writes_do_not_open_a_request_transaction(method, path):
    request = getattr(RequestFactory(), method)(path)
    observed = []

    def view(request):
        observed.append(connection.in_atomic_block)
        return Response({})

    RequestAuditContextMiddleware(view)(request)
    assert observed == [False]


@postgres_only
def test_read_does_not_wait_for_another_request_holding_the_session_lock(context):
    client, user, org, _ = context
    session = start(client, org)
    locked, release = Event(), Event()

    def hold_lock():
        close_old_connections()
        try:
            with transaction.atomic():
                SupportSession.objects.select_for_update().get(pk=session.pk)
                locked.set()
                assert release.wait(10)
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=1) as pool:
        holder = pool.submit(hold_lock)
        try:
            assert locked.wait(5)
            # The previous implementation would wait on the held row and time out.
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '1500ms'")
            token = Token.objects.create(user=user)
            client.force_authenticate(None)
            client.credentials(
                HTTP_AUTHORIZATION=f"Token {token.key}",
                HTTP_X_DWELLA_WORKSPACE=str(org.public_id),
            )
            assert client.get("/api/v1/properties/").status_code == 200
            assert client.get("/api/v1/accounts/me/").status_code == 200
        finally:
            release.set()
            holder.result(timeout=10)
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = 0")


@postgres_only
def test_write_revalidates_if_the_session_ends_after_its_initial_read(context):
    client, user, org, _ = context
    session = start(client, org)
    token = Token.objects.create(user=user)
    attempting_lock = Event()

    def write_property():
        close_old_connections()
        try:
            writer = APIClient()
            writer.credentials(
                HTTP_AUTHORIZATION=f"Token {token.key}",
                HTTP_X_DWELLA_WORKSPACE=str(org.public_id),
            )

            def observe(execute, sql, params, many, context):
                if "FOR UPDATE" in sql and "audit_supportsession" in sql:
                    attempting_lock.set()
                return execute(sql, params, many, context)

            with connection.execute_wrapper(observe):
                return writer.post(
                    "/api/v1/properties/", {"name": "Blocked", "address": "Plot 1"},
                    format="json",
                ).status_code
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            current = SupportSession.objects.select_for_update().get(pk=session.pk)
            writer = pool.submit(write_property)
            assert attempting_lock.wait(5)
            current.ended_at = timezone.now()
            current.save(update_fields=["ended_at"])
        assert writer.result(timeout=10) == 403
    assert not Property.objects.filter(name="Blocked").exists()
    assert not AuditEvent.objects.filter(action="support.create").exists()
