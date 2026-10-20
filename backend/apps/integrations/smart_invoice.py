"""Issue invoices and credit notes through ZRA Smart Invoice.

Billing calls `queue_sale_receipt` when an invoice is created and
`queue_refund_receipt` when one is voided. Both only reserve a receipt inside
the caller's transaction; the VSDC is called after commit, so a slow or
failed device never blocks or rolls back billing. Failed receipts keep their
invoice number and can be resent with `resend_receipts`.
"""

import logging
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from apps.billing.models import InvoiceLine
from apps.properties.models import Property

from .models import FiscalReceipt, SmartInvoiceSettings
from .zra import codes
from .zra.client import VsdcError, get_vsdc_client
from .zra.codes import TAX_RATES, TaxCategory

logger = logging.getLogger(__name__)
CENT = Decimal("0.01")
REGISTRANT = "Dwella"

# A refundable deposit is held for the tenant, not charged for a service, so it
# is left off the fiscal invoice.
FISCAL_KINDS = [
    InvoiceLine.Kind.RENT,
    InvoiceLine.Kind.LATE_FEE,
    InvoiceLine.Kind.UTILITY,
    InvoiceLine.Kind.OTHER,
]
# Item classification codes still need confirming against
# /itemClass/selectItemsClass once a live device is issued.
ITEM_CLASS = {
    InvoiceLine.Kind.RENT: "8013150000",
    InvoiceLine.Kind.LATE_FEE: "8013150000",
    InvoiceLine.Kind.UTILITY: "8310150000",
    InvoiceLine.Kind.OTHER: "8013150000",
}
COMMERCIAL_TYPES = {Property.PropertyType.COMMERCIAL}


def item_code(kind, category):
    """Stable itemCd (ZM + product type + packaging + quantity unit + number)."""
    number = FISCAL_KINDS.index(kind) * 10 + TaxCategory.values.index(category) + 1
    return f"ZM{codes.PRODUCT_TYPE_SERVICE}{codes.PACKAGING_NET}{codes.QUANTITY_UNIT}{number:07d}"


def money(value):
    return float(Decimal(value).quantize(CENT, ROUND_HALF_UP))


def tax_in(amount, category):
    """VAT inside a tax-inclusive amount (ZRA taxable amounts include the tax)."""
    rate = TAX_RATES[category]
    return (amount * rate / (100 + rate)).quantize(CENT, ROUND_HALF_UP)


def vsdc_time(value):
    return timezone.localtime(value).strftime("%Y%m%d%H%M%S")


def ready_settings(organization):
    config = SmartInvoiceSettings.objects.filter(organization=organization).first()
    return config if config and config.is_ready else None


def tax_category_for(config, invoice):
    unit = invoice.unit
    if unit and unit.property.property_type in COMMERCIAL_TYPES:
        return config.commercial_tax_category
    return config.residential_tax_category


def initialise_device(config):
    """Activate the VSDC for this branch and register Dwella's billable items."""
    client = get_vsdc_client()
    response = client.select_init_info(
        tpin=config.tpin, bhf_id=config.branch_id, device_serial=config.device_serial
    )
    info = response["data"]["info"]
    for kind in FISCAL_KINDS:
        for category in TaxCategory.values:
            client.save_items(
                {
                    "tpin": config.tpin,
                    "bhfId": config.branch_id,
                    "itemCd": item_code(kind, category),
                    "itemClsCd": ITEM_CLASS[kind],
                    "itemTyCd": codes.PRODUCT_TYPE_SERVICE,
                    "itemNm": f"{InvoiceLine.Kind(kind).label} ({category})",
                    "orgnNatCd": "ZM",
                    "pkgUnitCd": codes.PACKAGING_NET,
                    "qtyUnitCd": codes.QUANTITY_UNIT,
                    "vatCatCd": category,
                    "dftPrc": 0,
                    "isrcAplcbYn": "N",
                    "useYn": "Y",
                    "regrId": REGISTRANT,
                    "regrNm": REGISTRANT,
                    "modrId": REGISTRANT,
                    "modrNm": REGISTRANT,
                }
            )
    config.taxpayer_name = (info.get("taxprNm") or "")[:60]
    config.sdc_id = info.get("sdcId") or ""
    config.mrc_no = info.get("mrcNo") or ""
    config.last_invoice_number = max(config.last_invoice_number, info.get("lastSaleInvcNo") or 0)
    config.initialized_at = timezone.now()
    config.save()
    return config


def build_sale_payload(config, invoice, invoice_number):
    category = tax_category_for(config, invoice)
    lines = [line for line in invoice.lines.all() if line.kind in FISCAL_KINDS]
    items = []
    for seq, line in enumerate(lines, start=1):
        tax = tax_in(line.amount, category)
        items.append(
            {
                "itemSeq": seq,
                "itemCd": item_code(line.kind, category),
                "itemClsCd": ITEM_CLASS[line.kind],
                "itemNm": line.description[:200],
                "bcd": None,
                "pkgUnitCd": codes.PACKAGING_NET,
                "pkg": 1,
                "qtyUnitCd": codes.QUANTITY_UNIT,
                "qty": 1,
                "prc": money(line.amount),
                "splyAmt": money(line.amount),
                "dcRt": 0,
                "dcAmt": 0,
                "isrccCd": None,
                "isrccNm": None,
                "isrcRt": None,
                "isrcAmt": None,
                "vatCatCd": category,
                "iplCatCd": None,
                "tlCatCd": None,
                "exciseCatCd": None,
                "taxblAmt": money(line.amount),
                "vatAmt": money(tax),
                "totAmt": money(line.amount),
            }
        )
    total = sum((line.amount for line in lines), Decimal("0"))
    tax_total = sum((tax_in(line.amount, category) for line in lines), Decimal("0"))
    payload = {
        "tpin": config.tpin,
        "bhfId": config.branch_id,
        "invcNo": invoice_number,
        "orgInvcNo": 0,
        "custTpin": invoice.tenant.tpin or None,
        "custNm": invoice.tenant.full_name[:60],
        "salesTyCd": codes.SALES_TYPE_NORMAL,
        "rcptTyCd": codes.RECEIPT_SALE,
        "pmtTyCd": codes.PAYMENT_CREDIT,
        "salesSttsCd": codes.STATUS_APPROVED,
        "cfmDt": vsdc_time(timezone.now()),
        "salesDt": invoice.issue_date.strftime("%Y%m%d"),
        "stockRlsDt": None,
        "cnclReqDt": None,
        "cnclDt": None,
        "rfdDt": None,
        "rfdRsnCd": None,
        "totItemCnt": len(items),
    }
    for value in TaxCategory.values:
        suffix = codes.PAYLOAD_SUFFIX[value]
        used = value == category
        payload[f"taxblAmt{suffix}"] = money(total) if used else 0
        payload[f"taxRt{suffix}"] = float(TAX_RATES[value])
        payload[f"taxAmt{suffix}"] = money(tax_total) if used else 0
    payload.update(
        {
            "totTaxblAmt": money(total),
            "totTaxAmt": money(tax_total),
            "totAmt": money(total),
            "prchrAcptcYn": "N",
            "remark": invoice.reference,
            "regrId": REGISTRANT,
            "regrNm": REGISTRANT,
            "modrId": REGISTRANT,
            "modrNm": REGISTRANT,
            "itemList": items,
        }
    )
    return payload, total, tax_total


def next_invoice_number(config):
    locked = SmartInvoiceSettings.objects.select_for_update().get(pk=config.pk)
    locked.last_invoice_number += 1
    locked.save(update_fields=["last_invoice_number", "updated_at"])
    return locked.last_invoice_number


def queue_sale_receipt(invoice):
    """Reserve the ZRA invoice for a new invoice; sent once billing commits."""
    config = ready_settings(invoice.organization)
    if config is None or not invoice.lines.filter(kind__in=FISCAL_KINDS).exists():
        return None
    number = next_invoice_number(config)
    payload, total, tax_total = build_sale_payload(config, invoice, number)
    receipt = FiscalReceipt.objects.create(
        organization=invoice.organization,
        invoice=invoice,
        kind=FiscalReceipt.Kind.SALE,
        invoice_number=number,
        total=total,
        tax_total=tax_total,
        request_payload=payload,
    )
    transaction.on_commit(lambda: submit_receipt(receipt.pk))
    return receipt


def queue_refund_receipt(invoice):
    """Cancel a voided invoice with ZRA by issuing a credit note against it."""
    sale = (
        FiscalReceipt.objects.select_for_update()
        .filter(invoice=invoice, kind=FiscalReceipt.Kind.SALE)
        .first()
    )
    if sale is None or sale.status == FiscalReceipt.Status.CANCELLED:
        return None
    if sale.status != FiscalReceipt.Status.ISSUED:
        # ZRA never recorded it, so there is nothing to credit.
        sale.status = FiscalReceipt.Status.CANCELLED
        sale.save(update_fields=["status", "updated_at"])
        return None
    config = SmartInvoiceSettings.objects.get(organization=invoice.organization)
    number = next_invoice_number(config)
    now = vsdc_time(timezone.now())
    payload = {
        **sale.request_payload,
        "invcNo": number,
        "orgInvcNo": sale.invoice_number,
        "rcptTyCd": codes.RECEIPT_REFUND,
        "cfmDt": now,
        "salesDt": timezone.localdate().strftime("%Y%m%d"),
        "rfdDt": now,
        "rfdRsnCd": codes.REFUND_REASON_OTHER,
        "remark": f"Void of {invoice.reference}",
    }
    receipt = FiscalReceipt.objects.create(
        organization=invoice.organization,
        invoice=invoice,
        kind=FiscalReceipt.Kind.REFUND,
        invoice_number=number,
        original_invoice_number=sale.invoice_number,
        total=sale.total,
        tax_total=sale.tax_total,
        request_payload=payload,
    )
    transaction.on_commit(lambda: submit_receipt(receipt.pk))
    return receipt


def submit_receipt(receipt_id):
    """Send one receipt to the VSDC and record what came back. Never raises."""
    with transaction.atomic():
        receipt = FiscalReceipt.objects.select_for_update().get(pk=receipt_id)
        if receipt.status not in (FiscalReceipt.Status.PENDING, FiscalReceipt.Status.FAILED):
            return receipt
        receipt.attempts += 1
        try:
            response = get_vsdc_client().save_sales(receipt.request_payload)
        except VsdcError as error:
            receipt.status = FiscalReceipt.Status.FAILED
            receipt.error_code = error.code[:5]
            receipt.error_message = error.message[:255]
        except Exception:  # network or device outage: keep it for a resend
            logger.exception("Smart Invoice submission failed for receipt %s", receipt.pk)
            receipt.status = FiscalReceipt.Status.FAILED
            receipt.error_code = ""
            receipt.error_message = "The ZRA device could not be reached."
        else:
            data = response.get("data") or {}
            published = data.get("vsdcRcptPbctDate")
            receipt.status = FiscalReceipt.Status.ISSUED
            receipt.response_payload = response
            receipt.receipt_number = data.get("rcptNo")
            receipt.total_receipt_number = data.get("totRcptNo")
            receipt.internal_data = data.get("intrlData") or ""
            receipt.signature = data.get("rcptSign") or ""
            receipt.sdc_id = data.get("sdcId") or ""
            receipt.mrc_no = data.get("mrcNo") or ""
            receipt.issued_at = (
                timezone.make_aware(datetime.strptime(published, "%Y%m%d%H%M%S"))
                if published
                else timezone.now()
            )
            receipt.error_code = ""
            receipt.error_message = ""
        receipt.save()
        return receipt


def resend_receipts(queryset):
    """Retry receipts that have not reached ZRA yet. Returns how many issued."""
    issued = 0
    pending = queryset.filter(
        status__in=[FiscalReceipt.Status.PENDING, FiscalReceipt.Status.FAILED]
    ).values_list("pk", flat=True)
    for receipt_id in list(pending):
        if submit_receipt(receipt_id).status == FiscalReceipt.Status.ISSUED:
            issued += 1
    return issued
