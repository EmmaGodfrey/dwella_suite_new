from django.db import migrations
from django.db.models import Q


def merge_platform_tiers(apps, schema_editor):
    # Platform access is one tier: every staff or superuser account becomes both.
    User = apps.get_model("auth", "User")
    User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).update(
        is_staff=True, is_superuser=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_handyactionexecution"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(merge_platform_tiers, migrations.RunPython.noop),
    ]
