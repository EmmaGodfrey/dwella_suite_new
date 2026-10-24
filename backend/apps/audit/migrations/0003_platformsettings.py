from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("audit", "0002_supportsession")]
    operations = [migrations.CreateModel(
        name="PlatformSettings",
        fields=[
            ("id", models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False, serialize=False)),
            ("handy_agent_enabled", models.BooleanField(default=False)),
        ],
    )]
