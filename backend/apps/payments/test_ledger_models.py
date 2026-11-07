import pytest
from django.db import DatabaseError, connection, transaction

from .evidence import record_exchange
from .models import BalanceSnapshot, ProviderAccount, ProviderTransaction


@pytest.mark.django_db
def test_financial_tables_deny_external_readers_on_postgres():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL RLS")
    with connection.cursor() as cursor:
        for table in (
            "payments_provideraccount",
            "payments_providertransaction",
            "payments_balancesnapshot",
        ):
            cursor.execute("SELECT relrowsecurity FROM pg_class WHERE relname=%s", [table])
            assert cursor.fetchone()[0]


@pytest.mark.django_db
def test_retained_snapshot_and_imported_transactions_cannot_be_changed_on_postgres():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL evidence triggers")
    from django.utils import timezone

    account = ProviderAccount.objects.create(
        environment="sandbox", account_id="00000000-0000-0000-0000-000000000001", currency="ZMW"
    )
    exchange = record_exchange(environment="sandbox", operation="test", body=b"{}")
    ProviderTransaction.objects.create(
        account=account,
        provider_id="test-1",
        kind="credit",
        amount=1,
        posted_at=timezone.now(),
        content_digest="0" * 64,
        exchange=exchange,
    )
    BalanceSnapshot.objects.create(account=account, status="baseline")
    with pytest.raises(DatabaseError), transaction.atomic():
        ProviderTransaction.objects.update(amount=2)
    with pytest.raises(DatabaseError), transaction.atomic():
        BalanceSnapshot.objects.all().delete()
