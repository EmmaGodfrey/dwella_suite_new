from django.db import migrations


def drop_duplicate_originals(apps, schema_editor):
    """Unsigned documents held the same PDF twice; keep only `pdf`."""
    DocumentVersion = apps.get_model("documents", "DocumentVersion")
    DocumentVersion.objects.filter(signatures__isnull=True).exclude(unsigned_pdf=b"").update(
        unsigned_pdf=b""
    )


class Migration(migrations.Migration):
    dependencies = [("documents", "0003_private_signing_outbox")]

    operations = [migrations.RunPython(drop_duplicate_originals, migrations.RunPython.noop)]
