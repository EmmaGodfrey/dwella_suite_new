from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Invoice, InvoiceLine
from apps.billing.services import apply_late_fees, create_invoice, generate_rent_invoices
from apps.leases.services import create_lease
from apps.organizations.models import Organization, OrganizationMembership
from apps.properties.models import Property, Unit
from apps.tenants.models import Tenant

from .models import FiscalReceipt, SmartInvoiceSettings
from .smart_invoice import initialise_device
from .zra import codes
from .zra.client import FakeVsdcClient, VsdcError

User = get_user_model()
THIS_MONTH = timezone.localdate().replace(day=1)
SETTINGS_URL = "/api/v1/integrations/smart-invoice/"
INIT_URL = "/api/v1/integrations/smart-invoice/initialise/"


def member_client(organization, role, username):
    user = User.objects.create_user(username=username, password="StrongerPass123")
    OrganizationMembership.objects.create(organization=organization, user=user, role=role)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def org():
    return Organization.objects.create(name="Kafue Ridge Properties", address="Plot 12, Kafue Rd")


@pytest.fixture
def owner(org):
    return member_client(org, OrganizationMembership.Role.OWNER, "owner")


@pytest.fixture
def manager(org):
    return member_client(org, OrganizationMembership.Role.MANAGER, "manager")


@pytest.fixture
def connected(org):
    config = SmartInvoiceSettings.objects.create(
        organization=org, tpin="1002003004", device_serial="DWL-TEST-01"
    )
    initialise_device(config)
    config.enabled = True
    config.save()
    return config


def make_lease(org, unit_name="2A", phone="+260974123381", rent="3900.00", kind="apartment"):
    property_obj, _ = Property.objects.get_or_create(
        organization=org,
        name=f"{kind.title()} block",
        defaults={"property_type": kind, "address": "Plot 4471"},
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
        late_fee_percent=Decimal("5"),
        late_fee_grace_days=5,
        activate=True,
    )


def billed(org, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        generate_rent_invoices(org, THIS_MONTH)
    return Invoice.objects.get()


# Settings and device connection


@pytest.mark.django_db
def test_settings_start_unconfigured_and_simulated(manager):
    data = manager.get(SETTINGS_URL).json()["response_data"]
    assert data["configured"] is False
    assert data["device_mode"] == "simulated"
    assert {c["value"] for c in data["tax_categories"]} >= {"A", "D", "TOT"}


@pytest.mark.django_db
def test_only_owner_or_admin_can_change_settings(org, manager):
    viewer = member_client(org, OrganizationMembership.Role.VIEWER, "viewer")
    payload = {"tpin": "1002003004", "device_serial": "DWL-01"}
    assert manager.put(SETTINGS_URL, payload, format="json").status_code == 403
    assert manager.post(INIT_URL).status_code == 403
    assert viewer.get(SETTINGS_URL).status_code == 403
    assert APIClient().get(SETTINGS_URL).status_code in {401, 403}
    assert not SmartInvoiceSettings.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload, field",
    [
        ({"tpin": "12345", "device_serial": "DWL-01"}, "tpin"),
        ({"tpin": "10020030AB", "device_serial": "DWL-01"}, "tpin"),
        ({"tpin": "1002003004", "device_serial": "  "}, "device_serial"),
        ({"tpin": "1002003004", "device_serial": "DWL-01", "branch_id": "1"}, "branch_id"),
        ({"tpin": "1002003004", "device_serial": "DWL-01", "enabled": True}, "enabled"),
        ({"tpin": "1002003004", "device_serial": "DWL-01", "commercial_tax_category": "Z"},
         "commercial_tax_category"),
    ],
)  # fmt: skip
def test_settings_validation(owner, payload, field):
    response = owner.put(SETTINGS_URL, payload, format="json")
    assert response.status_code == 400
    assert field in response.json()["response_data"]


@pytest.mark.django_db
def test_connect_device_then_lock_its_details(owner):
    assert owner.post(INIT_URL).status_code == 400  # nothing saved yet
    saved = owner.put(
        SETTINGS_URL, {"tpin": "1002003004", "device_serial": "DWL-01"}, format="json"
    ).json()["response_data"]
    assert saved["settings"]["is_ready"] is False

    data = owner.post(INIT_URL).json()["response_data"]
    assert data["settings"]["is_ready"] is True
    assert data["settings"]["sdc_id"] == "SDC002003004"
    assert data["settings"]["mrc_no"] == "WIS02003004"
    assert owner.post(INIT_URL).status_code == 400  # already connected

    locked = owner.patch(SETTINGS_URL, {"tpin": "9998887776"}, format="json")
    assert locked.status_code == 400 and "tpin" in locked.json()["response_data"]
    paused = owner.patch(SETTINGS_URL, {"enabled": False}, format="json")
    assert paused.json()["response_data"]["settings"]["is_ready"] is False


@pytest.mark.django_db
def test_connect_reports_device_errors(owner, monkeypatch):
    owner.put(SETTINGS_URL, {"tpin": "1002003004", "device_serial": "DWL-01"}, format="json")

    def refuse(self, **kwargs):
        raise VsdcError(codes.RESULT_ALREADY_INSTALLED, "This device is installed")

    monkeypatch.setattr(FakeVsdcClient, "select_init_info", refuse)
    response = owner.post(INIT_URL)
    assert response.status_code == 400
    assert "This device is installed" in response.json()["response_data"]["device_serial"][0]
    assert SmartInvoiceSettings.objects.get().initialized_at is None


# Issuing invoices


@pytest.mark.django_db
def test_invoices_are_not_sent_when_smart_invoice_is_off(org, django_capture_on_commit_callbacks):
    make_lease(org)
    billed(org, django_capture_on_commit_callbacks)
    assert not FiscalReceipt.objects.exists()


@pytest.mark.django_db
def test_residential_rent_is_issued_exempt(
    org, manager, connected, django_capture_on_commit_callbacks
):
    make_lease(org)
    invoice = billed(org, django_capture_on_commit_callbacks)
    receipt = invoice.fiscal_receipts.get()
    assert receipt.status == FiscalReceipt.Status.ISSUED
    assert receipt.invoice_number == 1 and receipt.receipt_number == 1
    assert receipt.tax_total == Decimal("0.00")
    assert receipt.request_payload["itemList"][0]["vatCatCd"] == "D"
    assert receipt.request_payload["custNm"] == "Tenant 2A"
    assert receipt.signature and receipt.internal_data and receipt.sdc_id

    listed = manager.get("/api/v1/billing/invoices/").json()["response_data"][0]
    assert listed["fiscal_status"] == "issued"
    detail = manager.get(f"/api/v1/billing/invoices/{invoice.public_id}/").json()
    detail = detail["response_data"]
    assert detail["issuer"]["tpin"] == "1002003004"
    assert detail["fiscal_receipts"][0]["tax_category"] == "D"
    assert detail["fiscal_receipts"][0]["items"][0]["amount"] == "3900.00"


@pytest.mark.django_db
def test_commercial_rent_carries_vat_inside_the_price(
    org, connected, django_capture_on_commit_callbacks
):
    make_lease(org, kind="commercial", rent="11600.00")
    invoice = billed(org, django_capture_on_commit_callbacks)
    receipt = invoice.fiscal_receipts.get()
    assert invoice.total == Decimal("11600.00")  # tenant pays the same
    assert receipt.tax_total == Decimal("1600.00")  # 16/116 of the price
    assert receipt.request_payload["taxblAmtA"] == 11600.0
    assert receipt.request_payload["taxAmtA"] == 1600.0
    assert receipt.request_payload["taxblAmtD"] == 0


@pytest.mark.django_db
def test_deposits_are_left_off_the_fiscal_invoice(
    org, manager, connected, django_capture_on_commit_callbacks
):
    lease = make_lease(org)
    today = timezone.localdate()
    with django_capture_on_commit_callbacks(execute=True):
        deposit = create_invoice(
            organization=org,
            tenant=lease.tenant,
            lease=lease,
            issue_date=today,
            due_date=today,
            lines=[{"kind": "deposit", "description": "Deposit", "amount": Decimal("3900")}],
        )
        mixed = create_invoice(
            organization=org,
            tenant=lease.tenant,
            lease=lease,
            issue_date=today,
            due_date=today,
            lines=[
                {"kind": "deposit", "description": "Deposit", "amount": Decimal("3900")},
                {"kind": "utility", "description": "Water", "amount": Decimal("250")},
            ],
        )
    assert not deposit.fiscal_receipts.exists()
    assert mixed.fiscal_receipts.get().total == Decimal("250.00")
    response = manager.post(f"/api/v1/billing/invoices/{deposit.public_id}/send-to-zra/")
    assert response.status_code == 400


@pytest.mark.django_db
def test_failed_submission_is_kept_and_resent(
    org, manager, connected, monkeypatch, django_capture_on_commit_callbacks
):
    def offline(self, payload):
        raise ConnectionError("VSDC down")

    make_lease(org)
    with monkeypatch.context() as patch:
        patch.setattr(FakeVsdcClient, "save_sales", offline)
        invoice = billed(org, django_capture_on_commit_callbacks)
    receipt = invoice.fiscal_receipts.get()
    assert receipt.status == FiscalReceipt.Status.FAILED
    assert receipt.error_message == "The ZRA device could not be reached."
    assert manager.get(SETTINGS_URL).json()["response_data"]["unsent_receipts"] == 1

    response = manager.post(f"/api/v1/billing/invoices/{invoice.public_id}/send-to-zra/")
    assert response.status_code == 200
    assert response.json()["response_data"]["fiscal_status"] == "issued"
    receipt.refresh_from_db()
    assert receipt.invoice_number == 1 and receipt.attempts == 2


@pytest.mark.django_db
def test_invoice_issued_before_connecting_can_be_sent_later(
    org, owner, manager, django_capture_on_commit_callbacks
):
    make_lease(org)
    invoice = billed(org, django_capture_on_commit_callbacks)
    url = f"/api/v1/billing/invoices/{invoice.public_id}/send-to-zra/"
    assert manager.post(url).status_code == 400  # Smart Invoice is off
    owner.put(SETTINGS_URL, {"tpin": "1002003004", "device_serial": "DWL-01"}, format="json")
    owner.post(INIT_URL)
    assert manager.post(url).json()["response_data"]["fiscal_status"] == "issued"


# Voids and late fees


@pytest.mark.django_db
def test_voiding_an_issued_invoice_issues_a_credit_note(
    org, manager, connected, django_capture_on_commit_callbacks
):
    make_lease(org)
    invoice = billed(org, django_capture_on_commit_callbacks)
    with django_capture_on_commit_callbacks(execute=True):
        response = manager.post(f"/api/v1/billing/invoices/{invoice.public_id}/void/")
    refund = invoice.fiscal_receipts.get(kind=FiscalReceipt.Kind.REFUND)
    assert refund.status == FiscalReceipt.Status.ISSUED
    assert refund.invoice_number == 2 and refund.original_invoice_number == 1
    assert refund.request_payload["rcptTyCd"] == codes.RECEIPT_REFUND
    detail = manager.get(f"/api/v1/billing/invoices/{invoice.public_id}/").json()
    assert detail["response_data"]["fiscal_status"] == "credited"
    assert response.status_code == 200


@pytest.mark.django_db
def test_voiding_an_unsent_invoice_cancels_its_receipt(
    org, manager, connected, monkeypatch, django_capture_on_commit_callbacks
):
    make_lease(org)
    with monkeypatch.context() as patch:
        patch.setattr(FakeVsdcClient, "save_sales", lambda self, payload: 1 / 0)
        invoice = billed(org, django_capture_on_commit_callbacks)
    manager.post(f"/api/v1/billing/invoices/{invoice.public_id}/void/")
    assert invoice.fiscal_receipts.get().status == FiscalReceipt.Status.CANCELLED
    assert not invoice.fiscal_receipts.filter(kind=FiscalReceipt.Kind.REFUND).exists()


@pytest.mark.django_db
def test_late_fee_on_issued_invoice_goes_on_a_follow_up_invoice(
    org, connected, django_capture_on_commit_callbacks
):
    make_lease(org)
    invoice = billed(org, django_capture_on_commit_callbacks)
    late = invoice.due_date + timedelta(days=6)
    with django_capture_on_commit_callbacks(execute=True):
        assert apply_late_fees(org, today=late) == 1
    assert apply_late_fees(org, today=late + timedelta(days=10)) == 0  # not twice

    invoice.refresh_from_db()
    assert invoice.total == Decimal("3900.00")  # the issued invoice is untouched
    follow_up = Invoice.objects.get(charged_for=invoice)
    assert follow_up.total == Decimal("195.00")
    assert follow_up.lines.get().kind == InvoiceLine.Kind.LATE_FEE
    assert follow_up.fiscal_receipts.get().status == FiscalReceipt.Status.ISSUED


# The fake device itself


def sale_payload(**overrides):
    item = {
        "itemSeq": 1, "itemCd": "ZM3NTU0000001", "itemClsCd": "8013150000", "itemNm": "Rent",
        "pkgUnitCd": "NT", "pkg": 1, "qtyUnitCd": "U", "qty": 1, "prc": 116.0, "splyAmt": 116.0,
        "dcRt": 0, "dcAmt": 0, "vatCatCd": "A", "taxblAmt": 116.0, "vatAmt": 16.0, "totAmt": 116.0,
    }  # fmt: skip
    payload = {
        "tpin": "1002003004", "bhfId": "000", "invcNo": 7, "orgInvcNo": 0, "salesTyCd": "N",
        "rcptTyCd": "S", "salesSttsCd": "02", "cfmDt": "20261020120000", "salesDt": "20261020",
        "totItemCnt": 1, "totTaxblAmt": 116.0, "totTaxAmt": 16.0, "totAmt": 116.0,
        "prchrAcptcYn": "N", "regrId": "Dwella", "regrNm": "Dwella", "modrId": "Dwella",
        "modrNm": "Dwella", "itemList": [item],
    }  # fmt: skip
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    "overrides, code",
    [
        ({"tpin": "12"}, codes.RESULT_INVALID_DEVICE),
        ({"bhfId": "0"}, codes.RESULT_INVALID_DEVICE),
        ({"totAmt": 100.0}, codes.RESULT_PARAMETER_ERROR),
        ({"totTaxAmt": 15.0}, codes.RESULT_PARAMETER_ERROR),
        ({"totItemCnt": 2}, codes.RESULT_PARAMETER_ERROR),
        ({"cfmDt": None}, codes.RESULT_PARAMETER_ERROR),
        ({"itemList": []}, codes.RESULT_PARAMETER_ERROR),
        ({"rcptTyCd": "R"}, codes.RESULT_PARAMETER_ERROR),  # refund without orgInvcNo
    ],
)
def test_fake_device_rejects_malformed_sales(overrides, code):
    with pytest.raises(VsdcError) as error:
        FakeVsdcClient().save_sales(sale_payload(**overrides))
    assert error.value.code == code


def test_fake_device_signs_a_valid_sale():
    response = FakeVsdcClient().save_sales(sale_payload())
    assert response["resultCd"] == codes.RESULT_OK
    assert response["data"]["rcptNo"] == 7
    assert len(response["data"]["intrlData"]) == 26
    assert len(response["data"]["rcptSign"]) == 16


@pytest.mark.django_db
def test_tenant_tpin_must_be_ten_digits(org, manager):
    response = manager.post(
        "/api/v1/tenants/",
        {"full_name": "Chanda Stores Ltd", "phone_number": "+260971234567", "tpin": "12345"},
        format="json",
    )
    assert response.status_code == 400
    assert "tpin" in response.json()["response_data"]
