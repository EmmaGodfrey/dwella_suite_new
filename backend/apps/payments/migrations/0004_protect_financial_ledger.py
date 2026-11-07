from django.db import migrations


def protect(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for name in ("provideraccount", "providertransaction", "balancesnapshot"):
            table = f"payments_{name}"
            cursor.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", ["handy_agent"])
            if cursor.fetchone():
                cursor.execute(f'REVOKE ALL ON TABLE "{table}" FROM "handy_agent" CASCADE')
        for table in ("payments_providertransaction", "payments_balancesnapshot"):
            cursor.execute(f"""CREATE TRIGGER payments_immutable_record BEFORE UPDATE OR DELETE
                ON "{table}" FOR EACH ROW EXECUTE FUNCTION payments_immutable_exchange()""")


def reverse(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            for table in ("payments_providertransaction", "payments_balancesnapshot"):
                cursor.execute(f'DROP TRIGGER payments_immutable_record ON "{table}"')


class Migration(migrations.Migration):
    dependencies = [("payments", "0003_provideraccount_balancesnapshot_providertransaction")]
    operations = [migrations.RunPython(protect, reverse)]
