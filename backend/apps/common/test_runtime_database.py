"""Runtime login has DML/RLS access, while maintenance operations remain forbidden."""

from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError, connection, transaction
from django.utils import timezone
from psycopg import sql

from apps.billing.services import record_payment
from apps.notifications import test_whatsapp as base
from apps.notifications.test_whatsapp_documents import complete_tenant
from apps.notifications.whatsapp.access import actor_context
from apps.notifications.whatsapp.conversation import balance_snapshot
from apps.notifications.whatsapp.documents import descriptor, source
from apps.notifications.whatsapp.models import WhatsAppBinding

from .runtime_database import provision

pytestmark = pytest.mark.django_db(transaction=True)
config = base.config
house = base.house


def runtime_url(role="dwella_runtime_validation"):
    config = connection.settings_dict
    return (
        f"postgresql://{role}:synthetic-password-at-least-40-characters@"
        f"{config['HOST']}:{config['PORT'] or 5432}/{config['NAME']}"
    )


@pytest.mark.skipif(connection.vendor != "postgresql", reason="PostgreSQL role boundaries")
def test_restricted_runtime_can_read_private_work_and_record_payment_but_cannot_administer(house):
    role = "dwella_runtime_validation"
    complete_tenant(house)
    base.workspace(house)
    try:
        result = provision(runtime_url(role))
        assert result["private_tables"] >= 10
        assert provision(runtime_url(role)) == result
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
            call_command("check_runtime_database", stdout=StringIO())
            binding = WhatsAppBinding.objects.get()
            ctx = actor_context(binding, house["org"].pk)
            assert balance_snapshot(ctx)["count"] == 1
            before = source(ctx, descriptor("invoice", house["invoice"].public_id, house["org"]))
            assert Decimal(before["balance"]) == house["invoice"].balance
            payment = record_payment(
                invoice=house["invoice"],
                amount=Decimal("100"),
                method="cash",
                paid_on=timezone.localdate(),
                recorded_by=house["manager"],
            )
            assert payment.receipt_number
            after = source(ctx, descriptor("invoice", house["invoice"].public_id, house["org"]))
            assert Decimal(after["balance"]) == Decimal(before["balance"]) - Decimal("100")
            for statement in [
                "CREATE TABLE runtime_forbidden (id integer)",
                "ALTER TABLE billing_payment DISABLE TRIGGER ALL",
                "UPDATE django_migrations SET app=app",
                "CREATE ROLE runtime_forbidden",
            ]:
                with (
                    pytest.raises(DatabaseError),
                    transaction.atomic(),
                    connection.cursor() as cursor,
                ):
                    cursor.execute(statement)
    finally:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT c.relname FROM pg_class c JOIN pg_namespace n "
                "ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relrowsecurity"
            )
            for (table,) in cursor.fetchall():
                cursor.execute(
                    sql.SQL("DROP POLICY IF EXISTS dwella_runtime_access ON {}").format(
                        sql.Identifier(table)
                    )
                )
            cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def test_runtime_provisioning_errors_never_echo_the_password():
    secret = "synthetic-sensitive-password-do-not-echo"
    with (
        patch(
            "apps.common.management.commands.provision_runtime_database.provision",
            side_effect=ValueError(secret),
        ),
        pytest.raises(CommandError) as caught,
    ):
        call_command("provision_runtime_database", stdout=StringIO())
    assert secret not in str(caught.value)


def test_runtime_check_rejects_maintenance_connection():
    with pytest.raises(CommandError):
        call_command("check_runtime_database", stdout=StringIO())


@pytest.mark.parametrize("change", ["weak", "host", "role", "scheme"])
@pytest.mark.skipif(connection.vendor != "postgresql", reason="PostgreSQL role boundaries")
def test_runtime_provisioning_refuses_invalid_targets(change):
    value = runtime_url()
    if change == "weak":
        value = value.replace("synthetic-password-at-least-40-characters", "short")
    elif change == "host":
        value = value.replace(connection.settings_dict["HOST"], "other.invalid")
    elif change == "role":
        value = value.replace("dwella_runtime_validation", connection.settings_dict["USER"])
    else:
        value = value.replace("postgresql:", "https:")
    with pytest.raises(ValueError):
        provision(value)
