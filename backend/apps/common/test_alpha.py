"""External-alpha exceptions remain explicit, test-only, and money-free."""
import os
import subprocess
import sys
from io import StringIO
from unittest.mock import Mock

import pytest
from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.notifications.phone_messaging import phone_allowed


@pytest.mark.parametrize("environment", ["production", "staging", "development"])
def test_alpha_cannot_start_outside_test(environment):
    env = {**os.environ, "APP_ENVIRONMENT": environment, "APP_ALPHA_TEST_ENABLED": "true",
           "TEST_EMAIL_REDIRECT_TO": ""}
    result = subprocess.run(
        [sys.executable, "-c", "import config.settings"], env=env,
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "APP_ALPHA_TEST_ENABLED is restricted to test" in result.stderr


@pytest.mark.parametrize("alpha", ["true", "false"])
def test_alpha_disables_all_money_movement_even_if_provider_flags_are_true(alpha):
    env = {**os.environ, "APP_ENVIRONMENT": "test", "APP_ALPHA_TEST_ENABLED": alpha,
           "LENCO_PAYMENTS_ENABLED": "true", "LENCO_PAYOUTS_ENABLED": "true",
           "LENCO_AUTOMATIC_PAYOUTS": "true"}
    code = (
        "from config import settings as s; "
        "print(s.LENCO_PAYMENTS_ENABLED,s.LENCO_PAYOUTS_ENABLED,s.LENCO_AUTOMATIC_PAYOUTS)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True,
    )
    assert result.stdout.strip() == ("False False False" if alpha == "true" else "True True True")


@pytest.mark.django_db
def test_alpha_recipient_exception_is_test_only_bounded_and_keeps_default_guard(settings):
    settings.APP_ENVIRONMENT = "test"
    settings.OUTBOUND_PHONE_ALLOWLIST = ["+260971234567"]
    settings.ALPHA_TEST_ENABLED = False
    assert phone_allowed("+260971234567")
    assert not phone_allowed("+260972345678")
    settings.ALPHA_TEST_ENABLED = True
    with CaptureQueriesContext(connection) as queries:
        assert phone_allowed("+260972345678")
        for invalid in [None, "", "hello", "*", "+260 972345678", "972345678"]:
            assert not phone_allowed(invalid)
    assert len(queries) == 0
    settings.APP_ENVIRONMENT = "production"
    assert not phone_allowed("+260972345678")


@pytest.mark.django_db
@pytest.mark.parametrize("alpha", [True, False])
@pytest.mark.parametrize("command", ["run_messages", "run_operational_messages"])
def test_alpha_dispatches_explicit_work_without_scheduling_old_tenancies(
    settings, monkeypatch, alpha, command,
):
    import importlib

    module = importlib.import_module(f"apps.notifications.management.commands.{command}")
    schedule_name = "schedule_reminders" if command == "run_messages" else "schedule_operational"
    dispatch_name = "dispatch_messages" if command == "run_messages" else "dispatch_operational"
    scheduled, dispatched = Mock(return_value=0), Mock(return_value=0)
    monkeypatch.setattr(module, schedule_name, scheduled)
    monkeypatch.setattr(module, dispatch_name, dispatched)
    settings.ALPHA_TEST_ENABLED = alpha
    call_command(command, stdout=StringIO())
    assert scheduled.call_count == (0 if alpha else 1)
    dispatched.assert_called_once_with()
