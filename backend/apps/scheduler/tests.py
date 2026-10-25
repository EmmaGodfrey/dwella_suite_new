from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from .models import JobRun
from .services import STALE_AFTER, is_due, run_due_jobs, run_job

pytestmark = pytest.mark.django_db
LUSAKA = ZoneInfo("Africa/Lusaka")


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


def at(hour, minute=0, day=10):
    return datetime(2026, 11, day, hour, minute, tzinfo=LUSAKA)


def record(job, started, status=JobRun.Status.SUCCEEDED):
    return JobRun.objects.create(job=job, started_at=started, status=status)


def test_only_listed_jobs_run(settings):
    settings.SCHEDULER_JOBS = []
    with patch("apps.scheduler.services.call_command") as command:
        assert run_due_jobs(at(7)) == []
    command.assert_not_called()
    settings.SCHEDULER_JOBS = ["beta_emails", "not_a_job"]
    with patch("apps.scheduler.services.call_command") as command:
        runs = run_due_jobs(at(7))
    assert [run.job for run in runs] == ["beta_emails"]
    command.assert_called_once()


def test_interval_job_waits_for_its_interval():
    now = at(7)
    assert is_due("beta_emails", now)
    record("beta_emails", now - timedelta(minutes=10))
    assert not is_due("beta_emails", now)
    assert is_due("beta_emails", now + timedelta(minutes=6))


def test_daily_job_runs_once_after_its_time_and_retries_failures_with_a_cap():
    assert not is_due("billing", at(5, 59))
    assert is_due("billing", at(6))
    record("billing", at(6), JobRun.Status.FAILED)
    assert not is_due("billing", at(6, 20))
    assert is_due("billing", at(6, 31))
    record("billing", at(6, 31), JobRun.Status.FAILED)
    record("billing", at(7, 5), JobRun.Status.FAILED)
    assert not is_due("billing", at(9))
    assert is_due("billing", at(6, 1, day=11))
    record("billing", at(6, 1, day=11))
    assert not is_due("billing", at(23, day=11))


def test_yesterdays_run_does_not_cover_today():
    record("billing", at(23, day=9))
    assert is_due("billing", at(6, 5))


def test_failure_is_recorded_and_lock_released():
    with patch("apps.scheduler.services.call_command", side_effect=RuntimeError("smtp down")):
        run = run_job("beta_emails")
    assert run.status == "failed" and "RuntimeError" in run.detail and run.finished_at
    with patch("apps.scheduler.services.call_command"):
        assert run_job("beta_emails").status == "succeeded"


def test_overlapping_run_is_skipped():
    cache.add("scheduler:lock:billing", "1")
    with patch("apps.scheduler.services.call_command") as command:
        assert run_job("billing") is None
    command.assert_not_called()
    assert not JobRun.objects.exists()


def test_abandoned_running_rows_are_closed(settings):
    settings.SCHEDULER_JOBS = []
    now = at(12)
    old = record("billing", now - STALE_AFTER - timedelta(minutes=1), JobRun.Status.RUNNING)
    fresh = record("billing", now - timedelta(minutes=5), JobRun.Status.RUNNING)
    run_due_jobs(now)
    old.refresh_from_db()
    fresh.refresh_from_db()
    assert old.status == "failed" and fresh.status == "running"


def test_status_is_platform_admin_only():
    url = "/api/v1/platform/scheduler/status/"
    assert APIClient().get(url).status_code in {401, 403}
    user = get_user_model().objects.create_user(username="manager", email="m@example.com")
    client = APIClient()
    client.force_authenticate(user=user)
    assert client.get(url).status_code == 403
    admin = get_user_model().objects.create_user(
        username="admin", email="a@example.com", is_staff=True
    )
    client.force_authenticate(user=admin)
    record("billing", at(6), JobRun.Status.FAILED)
    response = client.get(url)
    assert response.status_code == 200, response.content
    jobs = {job["job"]: job for job in response.json()["response_data"]["jobs"]}
    assert jobs["billing"]["last_run"]["status"] == "failed"
    assert jobs["billing"]["schedule"] == "daily from 06:00"
