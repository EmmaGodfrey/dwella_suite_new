from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.leases.services import create_lease
from apps.organizations.models import Organization, OrganizationMembership
from apps.properties.models import Property, Unit
from apps.tenants.models import Tenant

from .models import Invoice, InvoiceLine, Payment
from .services import apply_late_fees, generate_rent_invoices, record_payment

User = get_user_model()
THIS_MONTH = timezone.localdate().replace(day=1)
THIS_PERIOD = f"{THIS_MONTH:%Y-%m}"


def member_client(organization, role, username):
    user = User.objects.create_user(username=username, password="StrongerPass123")
    OrganizationMembership.objects.create(organization=organization, user=user, role=role)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def org():
    return Organization.objects.create(name="Kafue Ridge Properties")


@pytest.fixture
def manager(org):
    return member_client(org, OrganizationMembership.Role.LANDLORD, "manager")


def make_lease(
    org, unit_name="2A", phone="+260974123381", rent="3900.00", late_fee="5", active=True
):
    property_obj, _ = Property.objects.get_or_create(
        organization=org,
        name="Mutendere Court",
        defaults={"property_type": "apartment", "address": "Plot 4471"},
    )
    unit = Unit.objects.create(
        organization=org, property=property_obj, name=unit_name, rent_amount=rent
    )
    tenant = Tenant.objects.create(
        organization=org, full_name=f"Tenant {unit_name}", phone_number=phone
    )
    return create_lease(
        organization=org,
        tenant=tenant,
        unit=unit,
        start_date=THIS_MONTH - timedelta(days=90),
        end_date=THIS_MONTH + timedelta(days=270),
        monthly_rent=Decimal(rent),
        late_fee_percent=Decimal(late_fee),
        late_fee_grace_days=5,
        activate=active,
    )


@pytest.mark.django_db
def test_generate_bills_active_leases_once(manager, org):
    lease = make_lease(org)
    make_lease(org, unit_name="2B", phone="+260975550000", active=False)  # draft: not billed

    first = manager.post(
        "/api/v1/billing/invoices/generate/", {"period": THIS_PERIOD}, format="json"
    )
    assert first.status_code == 200
    assert first.json()["response_data"]["created"] == 1
    again = manager.post(
        "/api/v1/billing/invoices/generate/", {"period": THIS_PERIOD}, format="json"
    )
    assert again.json()["response_data"]["created"] == 0
    assert again.json()["response_data"]["already_billed"] == 1

    invoice = Invoice.objects.get()
    assert invoice.reference == "INV-0001"
    assert invoice.lease == lease
    assert invoice.total == Decimal("3900.00")
    assert invoice.due_date == max(THIS_MONTH.replace(day=lease.rent_due_day), timezone.localdate())
    assert invoice.lines.get().kind == InvoiceLine.Kind.RENT


@pytest.mark.django_db
@pytest.mark.parametrize("period", ["2026/11", "2026-13", "nonsense", "2099-01"])
def test_generate_rejects_bad_or_far_future_periods(manager, period):
    response = manager.post("/api/v1/billing/invoices/generate/", {"period": period}, format="json")
    assert response.status_code == 400
    assert "period" in response.json()["response_data"]


@pytest.mark.django_db
def test_record_partial_then_full_payment(manager, org):
    make_lease(org)
    generate_rent_invoices(org, THIS_MONTH)
    invoice = Invoice.objects.get()
    url = f"/api/v1/billing/invoices/{invoice.public_id}/record-payment/"

    partial = manager.post(url, {"amount": "1000.00", "method": "cash"}, format="json")
    assert partial.status_code == 201
    data = partial.json()["response_data"]
    assert data["status"] == "partially_paid"
    assert data["balance"] == "2900.00"
    assert data["payments"][0]["receipt_number"] == "RCT-0001"
    assert data["payments"][0]["recorded_by_name"] == "manager"

    full = manager.post(
        url, {"amount": "2900.00", "method": "mobile_money", "reference": "MP241019"}, format="json"
    )
    assert full.json()["response_data"]["status"] == "paid"
    assert Payment.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload, field",
    [
        ({"amount": "5000.00", "method": "cash"}, "amount"),
        ({"amount": "0", "method": "cash"}, "amount"),
        ({"amount": "-10", "method": "cash"}, "amount"),
        ({"amount": "100.00", "method": "bitcoin"}, "method"),
        ({"amount": "100.00", "method": "cash", "paid_on": "2999-01-01"}, "paid_on"),
        ({"method": "cash"}, "amount"),
    ],
)
def test_record_payment_validation(manager, org, payload, field):
    make_lease(org)
    generate_rent_invoices(org, THIS_MONTH)
    invoice = Invoice.objects.get()
    response = manager.post(
        f"/api/v1/billing/invoices/{invoice.public_id}/record-payment/", payload, format="json"
    )
    assert response.status_code == 400
    assert field in response.json()["response_data"]
    assert not Payment.objects.exists()


@pytest.mark.django_db
def test_void_only_without_payments_and_regenerate_after_void(manager, org):
    make_lease(org)
    generate_rent_invoices(org, THIS_MONTH)
    invoice = Invoice.objects.get()
    assert (
        manager.post(f"/api/v1/billing/invoices/{invoice.public_id}/void/").json()["response_data"][
            "status"
        ]
        == "void"
    )
    assert manager.post(f"/api/v1/billing/invoices/{invoice.public_id}/void/").status_code == 400
    # A voided month can be billed again.
    assert generate_rent_invoices(org, THIS_MONTH) == (1, 0)

    paid = Invoice.objects.exclude(pk=invoice.pk).get()
    record_payment(invoice=paid, amount=Decimal("100"), method="cash", paid_on=timezone.localdate())
    assert manager.post(f"/api/v1/billing/invoices/{paid.public_id}/void/").status_code == 400
    assert (
        manager.post(
            f"/api/v1/billing/invoices/{paid.public_id}/record-payment/",
            {"amount": "1", "method": "cash"},
            format="json",
        ).status_code
        == 201
    )


@pytest.mark.django_db
def test_paying_a_void_invoice_is_rejected(manager, org):
    make_lease(org)
    generate_rent_invoices(org, THIS_MONTH)
    invoice = Invoice.objects.get()
    manager.post(f"/api/v1/billing/invoices/{invoice.public_id}/void/")
    response = manager.post(
        f"/api/v1/billing/invoices/{invoice.public_id}/record-payment/",
        {"amount": "10", "method": "cash"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_late_fee_added_once_after_grace_period(org):
    make_lease(org, late_fee="5")
    generate_rent_invoices(org, THIS_MONTH)
    invoice = Invoice.objects.get()
    assert apply_late_fees(org, today=invoice.due_date + timedelta(days=5)) == 0  # still in grace
    assert apply_late_fees(org, today=invoice.due_date + timedelta(days=6)) == 1
    assert apply_late_fees(org, today=invoice.due_date + timedelta(days=30)) == 0  # not twice
    invoice.refresh_from_db()
    assert invoice.total == Decimal("4095.00")
    assert invoice.lines.filter(kind=InvoiceLine.Kind.LATE_FEE).get().amount == Decimal("195.00")


@pytest.mark.django_db
def test_no_late_fee_when_paid_or_lease_has_none(org):
    make_lease(org, late_fee="0")
    make_lease(org, unit_name="2B", phone="+260975550000", late_fee="5")
    generate_rent_invoices(org, THIS_MONTH)
    paid = Invoice.objects.get(lease__unit__name="2B")
    record_payment(invoice=paid, amount=paid.total, method="cash", paid_on=timezone.localdate())
    assert apply_late_fees(org, today=THIS_MONTH + timedelta(days=60)) == 0


@pytest.mark.django_db
def test_manual_invoice_validation_and_scoping(manager, org):
    lease = make_lease(org)
    tenant = lease.tenant
    created = manager.post(
        "/api/v1/billing/invoices/",
        {
            "tenant": str(tenant.public_id),
            "due_date": f"{THIS_MONTH + timedelta(days=40)}",
            "lines": [
                {"kind": "utility", "description": "Water · October", "amount": "250.00"},
                {"kind": "other", "description": "Gate remote", "amount": "150.00"},
            ],
        },
        format="json",
    )
    assert created.status_code == 201
    assert created.json()["response_data"]["total"] == "400.00"

    no_lines = manager.post(
        "/api/v1/billing/invoices/",
        {"tenant": str(tenant.public_id), "due_date": "2030-01-01", "lines": []},
        format="json",
    )
    assert "lines" in no_lines.json()["response_data"]
    bad_line = manager.post(
        "/api/v1/billing/invoices/",
        {
            "tenant": str(tenant.public_id),
            "due_date": "2030-01-01",
            "lines": [{"description": "Refund", "amount": "-50"}],
        },
        format="json",
    )
    assert bad_line.status_code == 400

    other = Organization.objects.create(name="Other Landlord")
    foreign = Tenant.objects.create(
        organization=other, full_name="Foreign", phone_number="+260979999999"
    )
    stolen = manager.post(
        "/api/v1/billing/invoices/",
        {
            "tenant": str(foreign.public_id),
            "due_date": "2030-01-01",
            "lines": [{"description": "X", "amount": "10"}],
        },
        format="json",
    )
    assert stolen.status_code == 400

    someone_else = Tenant.objects.create(
        organization=org, full_name="Someone", phone_number="+260976660000"
    )
    mismatched = manager.post(
        "/api/v1/billing/invoices/",
        {
            "tenant": str(someone_else.public_id),
            "lease": str(lease.public_id),
            "due_date": "2030-01-01",
            "lines": [{"description": "X", "amount": "10"}],
        },
        format="json",
    )
    assert "lease" in mismatched.json()["response_data"]


@pytest.mark.django_db
def test_issued_invoice_only_note_is_editable_and_cannot_be_deleted(manager, org):
    make_lease(org)
    generate_rent_invoices(org, THIS_MONTH)
    invoice = Invoice.objects.get()
    url = f"/api/v1/billing/invoices/{invoice.public_id}/"
    response = manager.patch(
        url, {"notes": "Promised Friday", "due_date": "2030-01-01", "total": "1"}, format="json"
    )
    assert response.status_code == 200
    invoice.refresh_from_db()
    assert invoice.notes == "Promised Friday"
    assert invoice.due_date != date(2030, 1, 1)
    assert invoice.total == Decimal("3900.00")
    assert manager.delete(url).status_code == 405


@pytest.mark.django_db
def test_summary_and_filters(manager, org):
    make_lease(org)
    generate_rent_invoices(org, THIS_MONTH)
    invoice = Invoice.objects.get()
    record_payment(
        invoice=invoice, amount=Decimal("900"), method="cash", paid_on=timezone.localdate()
    )

    summary = manager.get("/api/v1/billing/invoices/summary/").json()["response_data"]
    assert Decimal(summary["billed_this_month"]) == Decimal("3900")
    assert Decimal(summary["collected_this_month"]) == Decimal("900")
    assert Decimal(summary["outstanding"]) == Decimal("3000")
    breakdown = summary["month_breakdown"]
    assert Decimal(breakdown["paid"]) == Decimal("900")
    # The parts add back up to what was billed this month.
    assert Decimal(breakdown["billed"]) == Decimal("3900")
    parts = ("paid", "not_yet_due", "overdue")
    assert sum(Decimal(breakdown[key]) for key in parts) == Decimal("3900")
    history = summary["history"]
    assert len(history) == 6
    assert history[-1]["month"] == summary["month"]
    assert Decimal(history[-1]["billed"]) == Decimal("3900")
    assert Decimal(history[-1]["collected"]) == Decimal("900")
    assert all(Decimal(row["billed"]) == 0 for row in history[:-1])
    assert manager.get("/api/v1/billing/invoices/?unpaid=true").json()["pagination"]["count"] == 1
    assert (
        manager.get(f"/api/v1/billing/payments/?invoice={invoice.public_id}").json()["pagination"][
            "count"
        ]
        == 1
    )

    tenant_row = manager.get("/api/v1/tenants/").json()["response_data"][0]
    assert tenant_row["balance"] == "3000.00"


@pytest.mark.django_db
def test_other_organization_and_tenant_access(org, manager):
    make_lease(org)
    generate_rent_invoices(org, THIS_MONTH)
    invoice = Invoice.objects.get()
    pay_url = f"/api/v1/billing/invoices/{invoice.public_id}/record-payment/"

    outsider = member_client(
        Organization.objects.create(name="Other"), OrganizationMembership.Role.LANDLORD, "outsider"
    )
    assert outsider.get(f"/api/v1/billing/invoices/{invoice.public_id}/").status_code == 404
    assert (
        outsider.post(pay_url, {"amount": "10", "method": "cash"}, format="json").status_code == 404
    )
    assert (
        outsider.get("/api/v1/billing/invoices/summary/").json()["response_data"]["outstanding"]
        == "0.00"
    )

    tenant_user = member_client(org, OrganizationMembership.Role.TENANT, "tenant-user")
    assert tenant_user.get("/api/v1/billing/invoices/").status_code == 403
    assert (
        tenant_user.post(pay_url, {"amount": "10", "method": "cash"}, format="json").status_code
        == 403
    )
    assert (
        tenant_user.post(
            "/api/v1/billing/invoices/generate/", {"period": THIS_PERIOD}, format="json"
        ).status_code
        == 403
    )
    assert APIClient().get("/api/v1/billing/payments/").status_code in {401, 403}
    assert not Payment.objects.exists()


@pytest.mark.django_db
def test_payments_endpoint_is_read_only(manager, org):
    assert (
        manager.post("/api/v1/billing/payments/", {"amount": "10"}, format="json").status_code
        == 405
    )


@pytest.mark.django_db
def test_run_billing_command_is_idempotent(org):
    make_lease(org)
    call_command("run_billing")
    call_command("run_billing")
    assert Invoice.objects.count() == 1


@pytest.mark.django_db
def test_one_failing_workspace_does_not_stop_the_billing_run(org):
    from unittest import mock

    from django.core.management.base import CommandError

    from apps.billing import services

    make_lease(org)
    broken = Organization.objects.create(name="Broken books")
    real = services.generate_rent_invoices

    def generate(organization, period):
        if organization == broken:
            raise RuntimeError("bad data")
        return real(organization, period)

    with mock.patch(
        "apps.billing.management.commands.run_billing.generate_rent_invoices", side_effect=generate
    ):
        with pytest.raises(CommandError, match="Broken books"):
            call_command("run_billing")
    assert Invoice.objects.filter(organization=org).count() == 1


@pytest.mark.django_db
def test_month_billed_late_is_not_due_before_it_is_issued(org):
    make_lease(org, late_fee="5")
    late_start = THIS_MONTH + timedelta(days=17)
    generate_rent_invoices(org, THIS_MONTH, today=late_start)
    invoice = Invoice.objects.get()
    assert invoice.issue_date == late_start
    assert invoice.due_date == late_start
    assert apply_late_fees(org, today=late_start + timedelta(days=1)) == 0


@pytest.mark.django_db
def test_summary_history_counts_rent_toward_its_period(manager, org):
    make_lease(org)
    last_month = (THIS_MONTH - timedelta(days=1)).replace(day=1)
    # Billed late, in this month, for last month's rent.
    generate_rent_invoices(org, last_month)
    summary = manager.get("/api/v1/billing/invoices/summary/").json()["response_data"]
    history = {row["month"]: Decimal(row["billed"]) for row in summary["history"]}
    assert history[last_month.isoformat()] == Decimal("3900")
    assert history[THIS_MONTH.isoformat()] == Decimal("0")
    assert Decimal(summary["month_breakdown"]["billed"]) == Decimal("0")
