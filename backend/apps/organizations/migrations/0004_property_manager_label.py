from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("organizations", "0003_landlord_and_tenant_roles")]
    operations = [migrations.AlterField(
        model_name="organizationmembership", name="role",
        field=models.CharField(max_length=20, choices=[("landlord", "Property manager"), ("tenant", "Tenant")]),
    )]
