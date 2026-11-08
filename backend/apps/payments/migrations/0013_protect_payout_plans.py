from django.db import migrations


def protect(apps, schema_editor):
    # Same boundary as the other payment tables: no access for the assistant role.
    # Deployment re-creates the runtime role's policy for every private table.
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('ALTER TABLE "payments_payoutplan" ENABLE ROW LEVEL SECURITY')
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", ["handy_agent"])
        if cursor.fetchone():
            cursor.execute('REVOKE ALL ON TABLE "payments_payoutplan" FROM "handy_agent" CASCADE')


class Migration(migrations.Migration):
    dependencies = [("payments", "0012_payout_timing")]

    operations = [migrations.RunPython(protect, migrations.RunPython.noop)]
