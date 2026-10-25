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
    "beta_emails": Job(command="send_beta_emails", every=timedelta(minutes=15)),
    "billing": Job(command="run_billing", daily_at=time(6, 0)),
}
