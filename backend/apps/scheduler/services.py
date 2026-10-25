import io
import logging
import traceback
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.db.models import Count
from django.utils import timezone

from apps.documents.models import SigningEmail

from .jobs import JOBS
from .models import JobRun

logger = logging.getLogger(__name__)
HEARTBEAT_KEY = "scheduler:heartbeat"
# A run still marked running after this long belongs to a scheduler that died.
STALE_AFTER = timedelta(hours=2)


def enabled_jobs():
    return [name for name in settings.SCHEDULER_JOBS if name in JOBS]


def is_due(name, now):
    job = JOBS[name]
    runs = JobRun.objects.filter(job=name)
    if job.every:
        return not runs.filter(started_at__gt=now - job.every).exists()
    local = timezone.localtime(now)
    if local.time() < job.daily_at:
        return False
    start = local.replace(
        hour=job.daily_at.hour, minute=job.daily_at.minute, second=0, microsecond=0
    )
    today = runs.filter(started_at__gte=start)
    if today.filter(status__in=[JobRun.Status.SUCCEEDED, JobRun.Status.RUNNING]).exists():
        return False
    failures = today.filter(status=JobRun.Status.FAILED)
    if failures.count() >= job.max_daily_attempts:
        return False
    return not failures.filter(started_at__gt=now - job.retry_after).exists()


def run_job(name):
    # The lock keeps a second scheduler (or a manual run) from overlapping this one.
    lock = f"scheduler:lock:{name}"
    if not cache.add(lock, "1", timeout=int(STALE_AFTER.total_seconds())):
        return None
    run = JobRun.objects.create(job=name, started_at=timezone.now())
    output = io.StringIO()
    try:
        call_command(JOBS[name].command, stdout=output, stderr=output)
        run.status = JobRun.Status.SUCCEEDED
        run.detail = output.getvalue()[-4000:]
    except Exception as error:
        run.status = JobRun.Status.FAILED
        run.detail = (output.getvalue()[-2000:] + "\n" + traceback.format_exc()[-2000:]).strip()
        logger.error("Scheduled job %s failed: %s", name, type(error).__name__)
    finally:
        run.finished_at = timezone.now()
        run.save(update_fields=["status", "detail", "finished_at"])
        cache.delete(lock)
    return run


def run_due_jobs(now=None):
    now = now or timezone.now()
    JobRun.objects.filter(status=JobRun.Status.RUNNING, started_at__lt=now - STALE_AFTER).update(
        status=JobRun.Status.FAILED, finished_at=now, detail="Scheduler stopped mid-run."
    )
    cache.set(HEARTBEAT_KEY, now.isoformat(), timeout=None)
    return [run for name in enabled_jobs() if is_due(name, now) and (run := run_job(name))]


def scheduler_status():
    jobs = []
    for name, job in JOBS.items():
        last = JobRun.objects.filter(job=name).first()
        jobs.append(
            {
                "job": name,
                "enabled": name in settings.SCHEDULER_JOBS,
                "schedule": f"every {int(job.every.total_seconds() // 60)} minutes"
                if job.every
                else f"daily from {job.daily_at:%H:%M}",
                "last_run": None
                if not last
                else {
                    "status": last.status,
                    "started_at": last.started_at,
                    "finished_at": last.finished_at,
                    "detail": last.detail,
                },
                "recent_failures": JobRun.objects.filter(
                    job=name,
                    status=JobRun.Status.FAILED,
                    started_at__gt=timezone.now() - timedelta(days=7),
                ).count(),
            }
        )
    counts = dict(SigningEmail.objects.values("status").annotate(total=Count("pk"))
                  .values_list("status", "total"))
    return {"heartbeat": cache.get(HEARTBEAT_KEY), "jobs": jobs,
            "signing_mailer": {"heartbeat": cache.get("signing-mailer:heartbeat"),
                               "counts": counts},
            "payments_worker": {"heartbeat": cache.get("payments-worker:heartbeat")}}
