from django.db import migrations, models


class Migration(migrations.Migration):
    """Replace the exact app-balance match with a landlord-coverage check."""

    dependencies = [("payments", "0007_schedule_checks_and_expiry")]

    operations = [
        migrations.RemoveField(model_name="provideraccount", name="app_opening_balance"),
        migrations.AddField(
            model_name="provideraccount",
            name="checked_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="provideraccount",
            name="full_scan_needed",
            field=models.BooleanField(default=False),
        ),
        migrations.RemoveField(model_name="balancesnapshot", name="app_expected_balance"),
        migrations.RemoveField(model_name="balancesnapshot", name="app_difference"),
        migrations.AddField(
            model_name="balancesnapshot",
            name="held_for_landlords",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=18),
        ),
        migrations.AddField(
            model_name="balancesnapshot",
            name="surplus",
            field=models.DecimalField(decimal_places=2, max_digits=18, null=True),
        ),
    ]
