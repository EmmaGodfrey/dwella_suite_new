from django.db import models


class BetaApplication(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    role = models.CharField(max_length=50)
    units = models.CharField(max_length=50)
    town = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )
    internal_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.phone})"
