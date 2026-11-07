from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("notifications", "0013_retain_media_cleanup_pointer")]

    operations = [
        migrations.AddField(
            "notificationphonelink",
            "verification_nonce",
            models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            "notificationphonelink", "auth_stamp", models.CharField(max_length=64, blank=True)
        ),
        migrations.AddField(
            "notificationphonelink", "delivery_status", models.CharField(max_length=12, blank=True)
        ),
        migrations.AddField(
            "notificationphonelink", "provider_id", models.CharField(max_length=160, blank=True)
        ),
    ]
