# Consolidated before first release on 2026-11-01.

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


def protect(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", ["handy_agent"])
        assistant_exists = bool(cursor.fetchone())
        for table in (
            "notifications_operationaldelivery", "notifications_operationalscan",
            "notifications_notificationphonelink",
        ):
            cursor.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            if assistant_exists:
                cursor.execute(f'REVOKE ALL ON TABLE "{table}" FROM "handy_agent" CASCADE')


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0008_private_phone_consent'),
        ('organizations', '0004_property_manager_label'),
        ('tenants', '0002_tenant_tpin'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OperationalScan',
            fields=[
                ('source', models.CharField(max_length=80, primary_key=True, serialize=False)),
                ('day', models.DateField()),
                ('after_id', models.PositiveBigIntegerField(default=0)),
                ('completed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='NotificationPhoneLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(choices=[('sms', 'SMS'), ('whatsapp', 'WhatsApp')], max_length=12)),
                ('phone', models.CharField(max_length=16)),
                ('token_hash', models.CharField(max_length=64, unique=True)),
                ('expires_at', models.DateTimeField()),
                ('consumed_at', models.DateTimeField(null=True)),
                ('verified_at', models.DateTimeField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OperationalDelivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('public_id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('identity', models.CharField(max_length=240, unique=True)),
                ('event', models.CharField(max_length=60)),
                ('target_model', models.CharField(max_length=60)),
                ('target_id', models.PositiveBigIntegerField()),
                ('target_state', models.CharField(blank=True, max_length=40)),
                ('audience', models.CharField(choices=[('manager', 'Manager'), ('tenant', 'Tenant')], max_length=8)),
                ('channel', models.CharField(choices=[('email', 'email'), ('sms', 'sms'), ('whatsapp', 'whatsapp')], max_length=12)),
                ('recipient', models.CharField(blank=True, max_length=254)),
                ('status', models.CharField(choices=[('held', 'Held'), ('queued', 'Queued'), ('sending', 'Sending'), ('sent', 'Accepted by provider'), ('delivered', 'Delivered'), ('read', 'Read'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('review', 'Needs review')], default='queued', max_length=12)),
                ('reason', models.CharField(blank=True, max_length=80)),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('available_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('claimed_at', models.DateTimeField(null=True)),
                ('claim_token', models.UUIDField(null=True)),
                ('sent_at', models.DateTimeField(null=True)),
                ('provider_id', models.CharField(blank=True, max_length=160)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)ss', to='organizations.organization')),
                ('recipient_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tenants.tenant')),
            ],
            options={
                'indexes': [models.Index(fields=['status', 'available_at', 'id'], name='operational_due_work'), models.Index(fields=['organization', '-created_at'], name='operational_workspace')],
                'constraints': [models.CheckConstraint(condition=models.Q(models.Q(('audience', 'manager'), ('tenant__isnull', True)), ('audience', 'tenant'), _connector='OR'), name='operational_recipient_shape')],
            },
        ),
        migrations.RunPython(protect, migrations.RunPython.noop),
    ]
