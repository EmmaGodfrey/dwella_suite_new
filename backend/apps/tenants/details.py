"""Onboarding completeness, shared by manual entry, imports and documents.

These are Dwella's document requirements, not verification by an ID/tax issuer.
Incomplete records remain usable for payments, repairs and existing documents.
"""

from rest_framework.exceptions import ValidationError

LABELS = {
    "full_name": "Full legal name",
    "phone_number": "Phone",
    "tpin": "TPIN",
    "national_id": "Identity document number",
    "billing_address": "Billing address",
    "identity_country": "Identity issuing country",
    "company_registration": "Company registration",
    "representative_name": "Authorised representative",
    "representative_phone": "Representative phone",
}


def missing_details(tenant):
    get = (
        tenant.get
        if isinstance(tenant, dict)
        else lambda key, default="": getattr(tenant, key, default)
    )
    fields = ["full_name", "phone_number", "tpin", "billing_address"]
    fields += (
        ["company_registration", "representative_name", "representative_phone"]
        if get("tenant_type", "individual") == "company"
        else ["national_id", "identity_country"]
    )
    return [
        {"field": key, "label": LABELS[key]} for key in fields if not str(get(key) or "").strip()
    ]


def require_document_details(tenant):
    missing = missing_details(tenant)
    if missing:
        raise ValidationError(
            {
                "tenant_details": ["Complete tenant details before issuing this document."],
                "missing_fields": [item["field"] for item in missing],
            }
        )


def receipt_missing_details(payment):
    # Existing recorded receipts remain available when tenant details change.
    if payment.created_at < payment.tenant.document_requirements_since:
        return []
    return missing_details(payment.tenant)
