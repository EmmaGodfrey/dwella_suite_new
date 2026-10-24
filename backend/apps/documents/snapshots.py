import json

from django.utils import timezone

from .rendering import digest


def fingerprint(data):
    return digest(json.dumps(data, sort_keys=True, ensure_ascii=False).encode())


def issuer(organization):
    return {
        "name": str(organization),
        "address": ", ".join(
            filter(None, [organization.address, organization.town, organization.country])
        ),
        "email": organization.email,
        "phone_number": organization.phone_number,
        "currency": organization.currency,
    }


def lease_source(lease):
    return {
        "reference": lease.reference,
        "issuer": issuer(lease.organization),
        "tenant_name": lease.tenant.full_name,
        "tenant_email": lease.tenant.email,
        "tenant_phone": lease.tenant.phone_number,
        "premises": f"{lease.unit.property.name} · {lease.unit.name}",
        "property_address": lease.unit.property.address,
        **{
            name: str(getattr(lease, name))
            for name in [
                "start_date",
                "end_date",
                "monthly_rent",
                "deposit_amount",
                "rent_due_day",
                "late_fee_percent",
                "late_fee_grace_days",
                "notice_period_months",
            ]
        },
    }


def invoice_source(invoice):
    return {
        "reference": invoice.reference,
        "issuer": issuer(invoice.organization),
        "tenant_name": invoice.tenant.full_name,
        "tenant_email": invoice.tenant.email,
        "tenant_phone": invoice.tenant.phone_number,
        "premises": f"{invoice.unit.property.name} · {invoice.unit.name}" if invoice.unit else "—",
        "property_address": invoice.unit.property.address if invoice.unit else "",
        "lease_reference": invoice.lease.reference if invoice.lease else "",
        "issue_date": str(invoice.issue_date),
        "due_date": str(invoice.due_date),
        "period": str(invoice.period_start) if invoice.period_start else "One-off charge",
        "status": invoice.get_status_display(),
        "total": str(invoice.total),
        "amount_paid": str(invoice.amount_paid),
        "balance": str(invoice.balance),
        "lines": [
            {
                "description": line.description,
                "kind": line.get_kind_display(),
                "amount": str(line.amount),
            }
            for line in invoice.lines.order_by("pk")
        ],
        "payments": [
            {
                "receipt": pay.receipt_number,
                "amount": str(pay.amount),
                "date": str(pay.paid_on),
                "method": pay.get_method_display(),
            }
            for pay in invoice.payments.filter(reversed_at__isnull=True).order_by("pk")
        ],
        "as_of": timezone.localdate().isoformat(),
    }
