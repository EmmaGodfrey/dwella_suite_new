from decimal import Decimal

from django.db.models import Count, F, IntegerField, Q, Sum, Value

from apps.billing.models import Invoice, Payment
from apps.common.workspaces import resolve_workspace

from .common import (
    ReportView,
    csv_response,
    money,
    organization_today,
    page_bounds,
    report_response,
    validate_scope,
)
from .serializers import StatementParameters

STATEMENT_BASIS = (
    "Restated current ledger by invoice issue date and payment date. Voided invoices and "
    "reversed payments are excluded using their current status, including later corrections. "
    "This is not a historical snapshot. A negative balance is a credit."
)
EVENT_FIELDS = (
    "event_id", "event_date", "event_kind", "event_public_id", "event_reference",
    "invoice_reference", "invoice_public_id", "property_name", "unit_name", "event_amount",
)
STATEMENT_HEADERS = [
    "date", "type", "reference", "invoice", "property", "unit", "debit", "credit", "balance",
    "tenant", "currency", "date_from", "date_to", "basis",
]


class TenantStatement:
    """Two bounded aggregates, an ordered SQL union, and at most two page-prefix sums."""

    def __init__(self, organization, tenant, params):
        self.organization, self.tenant, self.params = organization, tenant, params
        self.charges = Invoice.objects.for_organization(organization).filter(
            tenant=tenant, issue_date__lte=params["date_to"],
        ).exclude(status=Invoice.Status.VOID)
        self.credits = Payment.objects.for_organization(organization).filter(
            tenant=tenant, invoice__tenant=tenant, invoice__organization=organization,
            reversed_at__isnull=True,
            paid_on__lte=params["date_to"],
        ).exclude(invoice__status=Invoice.Status.VOID)
        if params.get("property"):
            self.charges = self.charges.filter(unit__property__public_id=params["property"])
            self.credits = self.credits.filter(
                invoice__unit__property__public_id=params["property"]
            )
        dates = params["date_from"], params["date_to"]
        charges = self.charges.aggregate(
            opening=Sum("total", filter=Q(issue_date__lt=dates[0])),
            amount=Sum("total", filter=Q(issue_date__range=dates)),
            count=Count("pk", filter=Q(issue_date__range=dates)),
        )
        credits = self.credits.aggregate(
            opening=Sum("amount", filter=Q(paid_on__lt=dates[0])),
            amount=Sum("amount", filter=Q(paid_on__range=dates)),
            count=Count("pk", filter=Q(paid_on__range=dates)),
        )
        self.opening = (charges["opening"] or Decimal(0)) - (credits["opening"] or Decimal(0))
        self.debits = charges["amount"] or Decimal(0)
        self.credits_total = credits["amount"] or Decimal(0)
        self.closing = self.opening + self.debits - self.credits_total
        self.count = charges["count"] + credits["count"]

    def events(self):
        dates = self.params["date_from"], self.params["date_to"]
        charges = self.charges.filter(issue_date__range=dates).order_by().annotate(
            event_id=F("pk"), event_date=F("issue_date"),
            event_kind=Value(0, output_field=IntegerField()), event_public_id=F("public_id"),
            event_reference=F("reference"), invoice_reference=F("reference"),
            invoice_public_id=F("public_id"), property_name=F("unit__property__name"),
            unit_name=F("unit__name"), event_amount=F("total"),
        ).values(*EVENT_FIELDS)
        credits = self.credits.filter(paid_on__range=dates).order_by().annotate(
            event_id=F("pk"), event_date=F("paid_on"),
            event_kind=Value(1, output_field=IntegerField()), event_public_id=F("public_id"),
            event_reference=F("receipt_number"), invoice_reference=F("invoice__reference"),
            invoice_public_id=F("invoice__public_id"),
            property_name=F("invoice__unit__property__name"), unit_name=F("invoice__unit__name"),
            event_amount=F("amount"),
        ).values(*EVENT_FIELDS)
        return charges.union(credits, all=True).order_by("event_date", "event_kind", "event_id")

    def balance_before(self, event):
        date, kind, key = event["event_date"], event["event_kind"], event["event_id"]
        charge_filter = Q(issue_date__lt=date)
        credit_filter = Q(paid_on__lt=date)
        if kind == 0:
            charge_filter |= Q(issue_date=date, pk__lt=key)
        else:
            charge_filter |= Q(issue_date=date)
            credit_filter |= Q(paid_on=date, pk__lt=key)
        charges = self.charges.filter(charge_filter).aggregate(amount=Sum("total"))["amount"]
        credits = self.credits.filter(credit_filter).aggregate(amount=Sum("amount"))["amount"]
        return (charges or Decimal(0)) - (credits or Decimal(0))

    def render(self, event, balance):
        amount = event["event_amount"]
        charge = event["event_kind"] == 0
        return {
            "id": str(event["event_public_id"]),
            "date": event["event_date"].isoformat(),
            "type": "charge" if charge else "payment",
            "reference": event["event_reference"],
            "invoice": event["invoice_reference"],
            "invoice_id": str(event["invoice_public_id"]),
            "property": event["property_name"] or "Unassigned",
            "unit": event["unit_name"] or "",
            "debit": money(amount if charge else 0),
            "credit": money(0 if charge else amount),
            "balance": money(balance),
        }

    def render_rows(self, events, opening):
        balance = opening
        for event in events:
            balance += event["event_amount"] * (1 if event["event_kind"] == 0 else -1)
            yield self.render(event, balance)

    def csv_rows(self):
        metadata = {
            "tenant": self.tenant.full_name, "currency": self.organization.currency,
            "date_from": self.params["date_from"].isoformat(),
            "date_to": self.params["date_to"].isoformat(), "basis": STATEMENT_BASIS,
        }
        boundary = {"reference": "", "invoice": "", "property": "", "unit": "",
                    "debit": "0.00", "credit": "0.00"}
        yield {**metadata, **boundary, "date": metadata["date_from"],
               "type": "opening_balance", "balance": money(self.opening)}
        for row in self.render_rows(self.events().iterator(chunk_size=500), self.opening):
            yield {**metadata, **row}
        yield {**metadata, **boundary, "date": metadata["date_to"],
               "type": "closing_balance", "balance": money(self.closing)}


class TenantStatementView(ReportView):
    def get(self, request):
        org = resolve_workspace(request)
        today = organization_today(org)
        params = StatementParameters(data=request.query_params, context={"today": today})
        params.is_valid(raise_exception=True)
        data = params.validated_data
        tenant = validate_scope(org, data)
        statement = TenantStatement(org, tenant, data)
        if data.get("export") == "csv":
            return csv_response(
                f"dwella-statement-{tenant.public_id}-{data['date_from']}-{data['date_to']}",
                STATEMENT_HEADERS, statement.csv_rows(),
                numeric_columns={"debit", "credit", "balance"},
            )
        offset, size, _, _ = page_bounds(data, statement.count)
        events = list(statement.events()[offset:offset + size])
        opening = statement.balance_before(events[0]) if offset and events else statement.opening
        return report_response(request, data, statement.count, {
            "rows": list(statement.render_rows(events, opening)),
            "tenant": {"id": str(tenant.public_id), "name": tenant.full_name,
                       "archived": not tenant.is_active},
            "totals": {"opening_balance": money(statement.opening),
                       "charges": money(statement.debits),
                       "payments": money(statement.credits_total),
                       "closing_balance": money(statement.closing)},
            "page_opening_balance": money(opening),
            "date_from": data["date_from"], "date_to": data["date_to"],
            "as_of": today, "currency": org.currency, "basis": STATEMENT_BASIS,
        })
