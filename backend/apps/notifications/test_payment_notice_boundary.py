# ruff: noqa: F811
"""Regression boundary only: payment implementation remains Claude-owned."""

from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.payments.models import Collection, Exchange
from apps.payments.testing import (  # noqa: F401
    checkout,
    configuration,
    home,
    signature,
    webhook_body,
)

pytestmark = pytest.mark.django_db(transaction=True)


def test_payment_webhook_commits_when_notice_enqueue_is_broken(home):
    row = checkout(home)
    body = webhook_body(row)
    with patch(
        "apps.notifications.events.enqueue", side_effect=RuntimeError("notice broken"),
    ) as send:
        response = APIClient().post(
            "/api/v1/payments/webhook/", body, content_type="application/json",
            HTTP_X_LENCO_SIGNATURE=signature(body),
        )
        row.status = "failed"
        row.save(update_fields=["status"])
    assert response.status_code == 200
    send.assert_not_called()
    assert Collection.objects.get(pk=row.pk).status == "failed"
    assert Exchange.objects.filter(collection=row, operation="webhook").exists()
