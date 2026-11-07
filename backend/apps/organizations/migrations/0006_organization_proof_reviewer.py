import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0005_workspace_auto_invoice"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="proof_reviewer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="organizations.organizationmembership",
            ),
        ),
    ]
