from django.db import migrations, models


def to_landlord(apps, schema_editor):
    # Dwella keeps two workspace roles. Every former owner/admin/manager/staff/viewer
    # membership becomes a landlord; tenant memberships are unchanged.
    Membership = apps.get_model("organizations", "OrganizationMembership")
    Membership.objects.exclude(role="tenant").update(role="landlord")


def to_owner(apps, schema_editor):
    Membership = apps.get_model("organizations", "OrganizationMembership")
    Membership.objects.filter(role="landlord").update(role="owner")


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0002_alter_organizationmembership_role"),
    ]

    operations = [
        migrations.RunPython(to_landlord, to_owner),
        migrations.AlterField(
            model_name="organizationmembership",
            name="role",
            field=models.CharField(
                choices=[("landlord", "Landlord"), ("tenant", "Tenant")], max_length=20,
            ),
        ),
    ]
