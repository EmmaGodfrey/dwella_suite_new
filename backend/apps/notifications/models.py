from django.conf import settings
from django.db import models


class NotificationRead(models.Model):
    """Personal acknowledgement of a live portfolio alert."""

    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user", "key"], name="unique_notification_read"
            )
        ]

    def __str__(self):
        return f"{self.user_id}: {self.key}"
