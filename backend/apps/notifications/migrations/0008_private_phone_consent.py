from django.db import migrations


def protect_consent(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('ALTER TABLE "notifications_phonemessagingconsent" ENABLE ROW LEVEL SECURITY')
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", ["handy_agent"])
        if cursor.fetchone():
            cursor.execute('REVOKE ALL ON TABLE "notifications_phonemessagingconsent" '
                           'FROM "handy_agent" CASCADE')


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0007_phonemessagingconsent_messagedelivery_delivered_at_and_more"),
    ]
    operations = [migrations.RunPython(protect_consent, migrations.RunPython.noop)]
