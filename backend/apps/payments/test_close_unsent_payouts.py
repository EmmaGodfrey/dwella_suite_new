import json
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.audit.models import AuditEvent

from .evidence import record_exchange
from .models import Payout
from .testing import paid
from .withdrawals import balance

pytestmark = pytest.mark.django_db
REASON = "Lenco refused it; the ledger shows no debit."


def stuck(home, state):
    paid(home)  # automatic payouts are on in these fixtures
    payout = Payout.objects.get()
    Payout.objects.filter(pk=payout.pk).update(status="review", issue="payout_details_mismatch")
    body = {"status": True, "data": {"status": state, "amount": "1.00"}}
    record_exchange(
        environment="sandbox",
        operation="payout_submit",
        body=json.dumps(body).encode(),
        http_status=200,
        payout=payout,
    )
    payout.refresh_from_db()
    return payout


def run(*args):
    out = StringIO()
    call_command("close_unsent_payouts", *args, stdout=out)
    return out.getvalue()


def test_a_refused_payout_returns_to_the_balance_with_an_audit_record(home):
    payout = stuck(home, "failed")
    held = balance(home["org"])["available"]
    assert "Dry run" in run(payout.reference, "--reason", REASON)
    payout.refresh_from_db()
    assert payout.status == "review" and not AuditEvent.objects.exists()
    run(payout.reference, "--reason", REASON, "--apply")
    payout.refresh_from_db()
    assert payout.status == "failed" and payout.issue == "closed_unsent"
    assert balance(home["org"])["available"] == held + payout.amount
    event = AuditEvent.objects.get(action="payment.payout_closed_unsent")
    assert event.metadata["reason"] == REASON and "failed" in event.metadata["evidence"]


def test_a_payout_lenco_may_have_sent_is_never_closed(home):
    payout = stuck(home, "pending")
    with pytest.raises(CommandError, match="possibly sent"):
        run(payout.reference, "--reason", REASON, "--apply")
    payout.refresh_from_db()
    assert payout.status == "review"


def test_unreadable_evidence_stops_the_command(home):
    payout = stuck(home, None)
    with pytest.raises(CommandError, match="no readable status"):
        run(payout.reference, "--reason", REASON, "--apply")


def test_only_review_payouts_with_a_reason_are_closed(home):
    payout = stuck(home, "failed")
    Payout.objects.filter(pk=payout.pk).update(status="successful")
    with pytest.raises(CommandError, match="not review"):
        run(payout.reference, "--reason", REASON, "--apply")
    with pytest.raises(CommandError, match="reason"):
        run(payout.reference, "--reason", "short", "--apply")
    assert Payout.objects.get().amount == Decimal(payout.amount)
