from django.db import migrations


def protect_messages(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for table in ("notifications_messagerequest", "notifications_messagedelivery", "notifications_reminderscan"):
            cursor.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", ["handy_agent"])
            if cursor.fetchone():
                cursor.execute(f'REVOKE ALL ON TABLE "{table}" FROM "handy_agent" CASCADE')


class Migration(migrations.Migration):
    dependencies = [("notifications", "0003_reminderscan_messagerequest_messagedelivery_and_more")]
    operations = [migrations.RunPython(protect_messages, migrations.RunPython.noop)]
