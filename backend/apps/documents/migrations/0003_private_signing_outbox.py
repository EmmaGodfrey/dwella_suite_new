from django.db import migrations


def protect_outbox(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        # The application role owns this table and bypasses default-deny RLS.
        # External database readers must never see delivery metadata or ciphertext.
        cursor.execute('ALTER TABLE "documents_signingemail" ENABLE ROW LEVEL SECURITY')
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", ["handy_agent"])
        if cursor.fetchone():
            cursor.execute('REVOKE ALL ON TABLE "documents_signingemail" FROM "handy_agent" CASCADE')


class Migration(migrations.Migration):
    dependencies = [("documents", "0002_signingemail")]
    operations = [migrations.RunPython(protect_outbox, migrations.RunPython.noop)]
