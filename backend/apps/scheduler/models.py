from django.db import models


class JobRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    job = models.CharField(max_length=64)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RUNNING)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True)
    # Command output or the exception summary, trimmed; never recipient data or secrets.
    detail = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["job", "-started_at"], name="job_run_recent")]

    def __str__(self):
        return f"{self.job} {self.status} {self.started_at:%Y-%m-%d %H:%M}"
