from django.db import migrations


def protect(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for name in ("destination", "collection", "payout", "exchange", "webhookreceipt"):
            table = f"payments_{name}"
            cursor.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", ["handy_agent"])
            if cursor.fetchone():
                cursor.execute(f'REVOKE ALL ON TABLE "{table}" FROM "handy_agent" CASCADE')
        cursor.execute("""
            CREATE FUNCTION payments_immutable_exchange() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Provider evidence is append-only'; END;
            $$ LANGUAGE plpgsql
        """)
        cursor.execute("""
            CREATE TRIGGER payments_immutable_exchange BEFORE UPDATE OR DELETE
            ON payments_exchange FOR EACH ROW EXECUTE FUNCTION payments_immutable_exchange()
        """)


def unprotect(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute('DROP TRIGGER payments_immutable_exchange ON payments_exchange')
            cursor.execute('DROP FUNCTION payments_immutable_exchange()')


class Migration(migrations.Migration):
    dependencies = [("payments", "0001_initial")]
    operations = [migrations.RunPython(protect, unprotect)]
