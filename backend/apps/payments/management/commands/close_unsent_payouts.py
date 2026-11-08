"""Close legacy payouts stuck in review that Lenco's evidence shows never sent.

A payout in review keeps its amount out of the workspace balance. When every
saved provider response shows the transfer was refused, failed or never
created, the money never left, so the payout is marked failed and the amount
returns to the balance. Anything Lenco ever called pending or successful is
refused here and needs a person with the Lenco statement. Dry run by default.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.audit.models import AuditEvent
from apps.payments.evidence import read_exchange
from apps.payments.models import Exchange, Payout

MAYBE_SENT = {"pending", "successful", "processing"}


def provider_states(payout):
    states = []
    for exchange in Exchange.objects.filter(payout=payout).order_by("created_at"):
        body = read_exchange(exchange)
        data = (body.get("response") or {}).get("data") if isinstance(body, dict) else None
        state = data.get("status") if isinstance(data, dict) else None
        states.append((exchange.operation, exchange.http_status, state))
    return states


class Command(BaseCommand):
    help = "Mark review payouts that Lenco never sent as failed (dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument("references", nargs="+")
        parser.add_argument("--reason", required=True)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, references, reason, apply, **options):
        if len(reason.strip()) < 10:
            raise CommandError("Give a reason of at least 10 characters.")
        for reference in references:
            with transaction.atomic():
                payout = (
                    Payout.objects.select_for_update()
                    .select_related("collection")
                    .filter(reference=reference)
                    .first()
                )
                if payout is None:
                    raise CommandError(f"{reference}: not found.")
                if payout.status != "review":
                    raise CommandError(f"{reference}: status is {payout.status}, not review.")
                states = provider_states(payout)
                if any(state in MAYBE_SENT for _, _, state in states):
                    raise CommandError(f"{reference}: Lenco reported it as possibly sent.")
                # Only an explicit refusal or failure counts; unreadable evidence stops here.
                if any(state is None and not (code or 0) >= 400 for _, code, state in states):
                    raise CommandError(f"{reference}: a Lenco response has no readable status.")
                summary = ", ".join(f"{op} {code} {state or '-'}" for op, code, state in states)
                self.stdout.write(f"{reference} K{payout.amount}: {summary or 'no responses'}")
                if not apply:
                    continue
                before = payout.issue
                payout.status, payout.issue, payout.next_check_at = "failed", "closed_unsent", None
                payout.save(update_fields=["status", "issue", "next_check_at", "updated_at"])
                AuditEvent.objects.create(
                    organization=payout.collection.organization,
                    action="payment.payout_closed_unsent",
                    resource_type=payout._meta.label_lower,
                    resource_id=str(payout.public_id),
                    metadata={
                        "reason": reason.strip(),
                        "issue_before": before,
                        "evidence": summary,
                    },
                )
                self.stdout.write(f"{reference}: marked failed; K{payout.amount} back in balance.")
        if not apply:
            self.stdout.write("Dry run: nothing changed. Add --apply to close these payouts.")
