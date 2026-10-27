from django.db import migrations, models


def normalize_roles(apps, schema_editor):
    application = apps.get_model("marketing", "BetaApplication")
    application.objects.using(schema_editor.connection.alias).exclude(
        role="Property manager"
    ).update(role="Property manager")


class Migration(migrations.Migration):
    dependencies = [("marketing", "0003_beta_email_sequence")]

    operations = [
        migrations.RunPython(normalize_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="betaapplication",
            name="role",
            field=models.CharField(
                choices=[("Property manager", "Property manager")],
                default="Property manager",
                max_length=50,
            ),
        ),
        migrations.AddConstraint(
            model_name="betaapplication",
            constraint=models.CheckConstraint(
                condition=models.Q(role="Property manager"), name="beta_property_manager_only"
            ),
        ),
    ]
