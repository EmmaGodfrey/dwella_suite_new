from django.db import migrations

TABLES = (
    "organizations_teaminvitation",
    "organizations_teaminvitation_properties",
    "organizations_propertyassignment",
    "organizations_coversession",
)


def protect(apps, schema_editor):
    # Who may work where, and unaccepted invitations, are private: no access
    # for the assistant role. Deployment re-creates the runtime role's policy
    # for every private table.
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", ["handy_agent"])
        assistant = cursor.fetchone()
        for table in TABLES:
            cursor.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            if assistant:
                cursor.execute(f'REVOKE ALL ON TABLE "{table}" FROM "handy_agent" CASCADE')


class Migration(migrations.Migration):
    dependencies = [("organizations", "0007_property_teams")]

    operations = [migrations.RunPython(protect, migrations.RunPython.noop)]
