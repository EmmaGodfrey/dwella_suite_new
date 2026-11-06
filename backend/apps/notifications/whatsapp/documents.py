"""Requested PDF copies. Read fresh records, bound work, and never publish a URL."""

import hashlib
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

from django.db import connection
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.billing.deposits import allocation
from apps.billing.models import Invoice, Payment
from apps.documents.rendering import WIDTH, build, invoice_pdf, p, rule, table
from apps.documents.services import validate_pdf_size
from apps.documents.snapshots import fingerprint, invoice_source, issuer
from apps.reports.common import organization_today
from apps.reports.statements import STATEMENT_BASIS, TenantStatement
from apps.tenants.details import LABELS, require_document_details
from apps.tenants.models import Tenant

MAX_EVENTS = 300
MAX_INVOICE_LINES = 100
MAX_INVOICE_PAYMENTS = 100
DAILY_LIMIT = 12


def preparation_failure(ctx, error):
    """Explain document requirements without leaking internal exception values."""
    if isinstance(error.detail, dict) and "missing_fields" in error.detail:
        labels = [LABELS[field] for field in error.detail["missing_fields"] if field in LABELS]
        fields = ", ".join(labels)
        instruction = (
            "Ask your property manager to complete your tenant details in Dwella."
            if ctx.role == "tenant" else
            "Open Tenants in Dwella and complete this tenant's details, then request the PDF again."
        )
        return f"The invoice PDF needs complete tenant details: {fields}. {instruction}"
    return "This PDF could not be prepared here. Open it in Dwella."


def available(ctx, document):
    if not isinstance(document, dict):
        return False
    try:
        target = UUID(document["target"])
        kind = document["kind"]
        if kind == "statement":
            start = date.fromisoformat(document["date_from"])
            end = date.fromisoformat(document["date_to"])
            return bool(
                ctx.role == "tenant"
                and 0 <= (end - start).days <= 31
                and end <= organization_today(ctx.organization)
                and Tenant.objects.filter(
                    pk__in=ctx.tenant_ids,
                    public_id=target,
                    is_active=True,
                    organization=ctx.organization,
                ).exists()
            )
        if kind == "invoice":
            return (
                ctx.scope(Invoice.objects.all())
                .filter(
                    public_id=target,
                    tenant__organization=ctx.organization,
                )
                .exclude(status="void")
                .exists()
            )
        if kind == "receipt":
            return (
                ctx.scope(Payment.objects.all())
                .filter(
                    public_id=target,
                    reversed_at__isnull=True,
                    invoice__organization=ctx.organization,
                    invoice__tenant_id=F("tenant_id"),
                    tenant__organization=ctx.organization,
                )
                .exclude(invoice__status="void")
                .exists()
            )
    except (KeyError, TypeError, ValueError, AttributeError):
        return False
    return False


def request(ctx, conversation, kind, target):
    from datetime import timedelta

    from .conversation import menu, response, website
    from .models import WhatsAppReply

    if (
        WhatsAppReply.objects.filter(
            binding=ctx.binding,
            created_at__gte=timezone.now() - timedelta(days=1),
            view__has_key="document",
        ).count()
        >= DAILY_LIMIT
    ):
        return menu(
            ctx, conversation, "PDF request limit reached. Download other copies in Dwella."
        )
    document = descriptor(kind, target, ctx.organization)
    if not available(ctx, document):
        raise PermissionDenied("This document is no longer available.")
    path = (
        "billing/statement"
        if kind == "statement"
        else f'billing/{"invoices" if kind == "invoice" else "receipts"}/{target}'
    )
    view = response(
        "Your requested PDF copy. You can also open it securely in Dwella: " + website(path)
    )
    view["document"] = document
    return view


def descriptor(kind, target, organization):
    result = {"kind": kind, "target": str(target)}
    if kind == "statement":
        today = organization_today(organization)
        result.update(date_from=str(today.replace(day=1)), date_to=str(today))
    return result


def source(ctx, document):
    """No renderer or external I/O; also used after upload to detect corrections."""
    kind, target = document["kind"], document["target"]
    if kind == "invoice":
        row = (
            ctx.scope(Invoice.objects.all())
            .filter(
                tenant__organization=ctx.organization,
            )
            .exclude(status="void")
            .select_related(
                "organization",
                "tenant",
                "unit__property",
                "lease",
            )
            .filter(public_id=target)
            .first()
        )
        if not row:
            raise PermissionDenied("This invoice is no longer available.")
        if row.lines.count() > MAX_INVOICE_LINES or row.payments.count() > MAX_INVOICE_PAYMENTS:
            raise ValidationError("Download this large invoice from Dwella.")
        require_document_details(row.tenant)
        return invoice_source(row)
    if kind == "receipt":
        row = (
            ctx.scope(Payment.objects.all())
            .filter(
                public_id=target,
                reversed_at__isnull=True,
                invoice__organization=ctx.organization,
                invoice__tenant_id=F("tenant_id"),
                tenant__organization=ctx.organization,
            )
            .exclude(invoice__status="void")
            .select_related(
                "organization",
                "tenant",
                "invoice__unit__property",
            )
            .first()
        )
        if not row:
            raise PermissionDenied("This receipt is no longer available.")
        if row.invoice.lines.count() > MAX_INVOICE_LINES:
            raise ValidationError("Download this large receipt from Dwella.")
        return {
            "reference": row.receipt_number,
            "issuer": issuer(ctx.organization),
            "tenant": row.tenant.full_name,
            "invoice": row.invoice.reference,
            "amount": str(row.amount),
            "paid_on": str(row.paid_on),
            "method": row.get_method_display(),
            "payment_reference": row.reference,
            "allocation": allocation(row),
            "premises": (
                f"{row.invoice.unit.property.name} · {row.invoice.unit.name}"
                if row.invoice.unit
                else "Unassigned"
            ),
        }
    if kind == "statement" and ctx.role == "tenant":
        tenant = Tenant.objects.filter(
            pk__in=ctx.tenant_ids,
            organization=ctx.organization,
            public_id=target,
            is_active=True,
        ).first()
        if not tenant:
            raise PermissionDenied("This tenant account is no longer available.")
        start, end = (
            date.fromisoformat(document["date_from"]),
            date.fromisoformat(document["date_to"]),
        )
        if end < start or (end - start).days > 31 or end > organization_today(ctx.organization):
            raise ValidationError("Choose a current statement period in Dwella.")
        statement = TenantStatement(ctx.organization, tenant, {"date_from": start, "date_to": end})
        if statement.count > MAX_EVENTS:
            raise ValidationError("Download this larger statement from Dwella.")
        return {
            "reference": "Tenant statement",
            "issuer": issuer(ctx.organization),
            "tenant": tenant.full_name,
            "date_from": str(start),
            "date_to": str(end),
            "opening": f"{statement.opening:.2f}",
            "closing": f"{statement.closing:.2f}",
            "charges": f"{statement.debits:.2f}",
            "payments": f"{statement.credits_total:.2f}",
            "rows": list(statement.render_rows(statement.events()[:MAX_EVENTS], statement.opening)),
        }
    raise PermissionDenied("This document is not available for this account.")


def render(kind, snapshot):
    currency = snapshot["issuer"]["currency"]
    money = lambda value: f"{currency} {Decimal(value):,.2f}"  # noqa: E731
    if kind == "invoice":
        return invoice_pdf(snapshot)
    flow = [
        p(snapshot["issuer"]["name"], "heading"),
        p(snapshot["reference"], "title"),
        p(snapshot["tenant"], "strong"),
        rule(),
    ]
    if kind == "receipt":
        flow += [
            p(money(snapshot["amount"]), "balance"),
            p(f"Paid {snapshot['paid_on']} · {snapshot['method']}"),
            p(f"Invoice: {snapshot['invoice']}"),
            p(snapshot["premises"]),
            p(f"Payment reference: {snapshot['payment_reference'] or '—'}"),
        ]
        rows = [[p("Applied to"), p("Amount")]]
        rows += [
            [p(f"{row['label']}\n{row['note']}"), p(money(row["amount"]))]
            for row in snapshot["allocation"]
        ]
        flow += [
            table(rows, [WIDTH * 0.7, WIDTH * 0.3], headings=True),
            p("Copy of a recorded payment. No new payment is made by this document.", "small"),
        ]
    else:
        flow += [
            p(f"{snapshot['date_from']} to {snapshot['date_to']}"),
            p(f"Opening: {money(snapshot['opening'])}"),
            p(f"Charges: {money(snapshot['charges'])} · Payments: {money(snapshot['payments'])}"),
            p(f"Closing: {money(snapshot['closing'])}", "strong"),
        ]
        rows = [
            [
                p(value, "small")
                for value in ["Date / reference", "Home", "Charge", "Payment", "Balance"]
            ]
        ]
        rows += [
            [
                p(f"{row['date']}\n{row['reference']}", "small"),
                p(f"{row['property']} · {row['unit']}", "small"),
                p(row["debit"], "small"),
                p(row["credit"], "small"),
                p(row["balance"], "small"),
            ]
            for row in snapshot["rows"]
        ]
        flow += [
            table(rows, [WIDTH * ratio for ratio in [0.25, 0.27, 0.16, 0.16, 0.16]], headings=True),
            p(STATEMENT_BASIS, "small"),
            p("Deposits are shown separately.", "small"),
        ]
    return build(flow, f"Current ledger copy · {snapshot['reference']}")


def prepare(ctx, document):
    if connection.in_atomic_block:
        raise RuntimeError("PDF rendering must run outside a transaction.")
    snapshot = source(ctx, document)
    raw, pages = render(document["kind"], snapshot)
    validate_pdf_size(raw, pages)
    # Filenames contain only an opaque digest, not unchecked tenant/reference text.
    name = f"dwella-{document['kind']}-{hashlib.sha256(raw).hexdigest()[:12]}.pdf"
    return SimpleNamespace(
        content=raw, content_type="application/pdf", name=name, public_id=name
    ), fingerprint(snapshot)


def current(ctx, document, expected):
    return fingerprint(source(ctx, document)) == expected
