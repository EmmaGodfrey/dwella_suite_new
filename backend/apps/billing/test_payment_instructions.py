# ruff: noqa: F811  (org/manager fixtures are imported from .tests)
"""Ways tenants pay the workspace directly, printed on every invoice."""

import pypdfium2
import pytest

from apps.audit.models import AuditEvent
from apps.documents.rendering import invoice_pdf
from apps.documents.snapshots import invoice_source
from apps.organizations.models import Organization, OrganizationMembership

from .models import Invoice, PaymentInstruction
from .services import generate_rent_invoices
from .tests import THIS_MONTH, make_lease, manager, member_client, org  # noqa: F401

pytestmark = pytest.mark.django_db
URL = "/api/v1/billing/payment-instructions/"
BANK = {
    "kind": "bank",
    "account_name": "Kafue Ridge Properties Ltd",
    "bank_name": "Zanaco",
    "branch": "Cairo Road",
    "account_number": "0123 4567 8901",
}
MOMO = {
    "kind": "mobile_money",
    "account_name": "Kafue Ridge Properties",
    "network": "airtel",
    "phone": "0977 123 456",
}


def pdf_text(raw):
    document = pypdfium2.PdfDocument(raw)
    return "\n".join(page.get_textpage().get_text_range() for page in document)


def test_manager_adds_bank_and_mobile_money_details(manager):
    bank = manager.post(URL, BANK, format="json")
    assert bank.status_code == 201
    assert bank.json()["response_data"]["account_number"] == "012345678901"
    momo = manager.post(URL, MOMO, format="json")
    assert momo.status_code == 201
    assert momo.json()["response_data"]["phone"] == "0977123456"
    listed = manager.get(URL).json()["response_data"]
    assert [row["kind"] for row in listed] == ["bank", "mobile_money"]


def test_details_are_checked_for_their_kind(manager):
    reply = manager.post(URL, {**BANK, "account_number": "12-ab", "bank_name": ""}, format="json")
    assert reply.status_code == 400
    assert {"account_number", "bank_name"} <= set(reply.json()["response_data"])
    reply = manager.post(URL, {**MOMO, "phone": "12345", "network": ""}, format="json")
    assert {"phone", "network"} <= set(reply.json()["response_data"])
    # Switching kind clears the other kind's fields, so stale numbers never print.
    row = manager.post(URL, BANK, format="json").json()["response_data"]
    changed = manager.patch(f"{URL}{row['id']}/", MOMO, format="json").json()["response_data"]
    assert (changed["bank_name"], changed["account_number"]) == ("", "")


def test_at_most_three_ways_to_pay(manager):
    for _ in range(3):
        assert manager.post(URL, MOMO, format="json").status_code == 201
    assert manager.post(URL, MOMO, format="json").status_code == 400


def test_other_workspaces_never_see_or_change_them(manager):
    row = manager.post(URL, BANK, format="json").json()["response_data"]
    other = Organization.objects.create(name="Elsewhere Homes")
    outsider = member_client(other, OrganizationMembership.Role.LANDLORD, "outsider")
    assert outsider.get(URL).json()["response_data"] == []
    assert outsider.patch(f"{URL}{row['id']}/", MOMO, format="json").status_code == 404
    assert outsider.delete(f"{URL}{row['id']}/").status_code == 404


def test_every_change_is_audited(manager):
    row = manager.post(URL, BANK, format="json").json()["response_data"]
    manager.patch(f"{URL}{row['id']}/", {"branch": "Manda Hill"}, format="json")
    manager.delete(f"{URL}{row['id']}/")
    actions = set(AuditEvent.objects.values_list("action", flat=True))
    assert {
        "billing.payment_instruction_added",
        "billing.payment_instruction_changed",
        "billing.payment_instruction_removed",
    } <= actions


def test_invoice_prints_the_details_and_the_reference(manager, org, settings):
    settings.LENCO_PAYMENTS_ENABLED = True
    manager.post(URL, BANK, format="json")
    manager.post(URL, MOMO, format="json")
    make_lease(org)
    generate_rent_invoices(org, THIS_MONTH)
    snapshot = {**invoice_source(Invoice.objects.get()), "version": 1}
    text = pdf_text(invoice_pdf(snapshot)[0])
    for expected in (
        "How to pay",
        "Pay online",
        "Zanaco",
        "012345678901",
        "Airtel Money",
        "0977123456",
        snapshot["reference"],
    ):
        assert expected in text


def test_invoice_without_details_falls_back_to_asking_the_manager(org, settings):
    settings.LENCO_PAYMENTS_ENABLED = False
    make_lease(org)
    generate_rent_invoices(org, THIS_MONTH)
    snapshot = {**invoice_source(Invoice.objects.get()), "version": 1}
    text = pdf_text(invoice_pdf(snapshot)[0])
    assert "provided by your property manager" in text
    assert "Pay online" not in text
    assert not PaymentInstruction.objects.exists()
