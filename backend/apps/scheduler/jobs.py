"""Recurring jobs. Add a module's job here, then enable it per environment
with APP_SCHEDULER_JOBS so nothing new runs in production by surprise."""

from dataclasses import dataclass
from datetime import time, timedelta


@dataclass(frozen=True)
class Job:
    command: str
    # Either repeat every `every`, or run once a day from `daily_at` (Lusaka time).
    every: timedelta | None = None
    daily_at: time | None = None
    # How long to wait before trying a failed daily job again the same day.
    retry_after: timedelta = timedelta(minutes=30)
    max_daily_attempts: int = 3


JOBS = {
    "lenco_payments": Job(command="process_lenco_payments", every=timedelta(seconds=30)),
    "lenco_finances": Job(command="sync_lenco_finances", every=timedelta(minutes=5)),
    "beta_emails": Job(command="send_beta_emails", every=timedelta(minutes=15)),
    # Before billing, so a renewal that starts today is the lease that gets billed.
    "renewals": Job(command="start_renewals", daily_at=time(5, 30)),
    "billing": Job(command="run_billing", daily_at=time(6, 0)),
    "offsite_backups": Job(command="upload_backups", every=timedelta(hours=1)),
    "media_snapshots": Job(command="snapshot_media", daily_at=time(0, 5)),
}
