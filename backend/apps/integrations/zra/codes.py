"""Code tables from the ZRA VSDC API documentation (v1.0.2, chapter 4)."""

from decimal import Decimal

from django.db import models


class TaxCategory(models.TextChoices):
    # 4.1 Tax Type. The letter is sent as `vatCatCd` on every item.
    STANDARD = "A", "Standard rated 16%"
    MINIMUM_TAXABLE_VALUE = "B", "Minimum taxable value 16%"
    EXPORTS = "C1", "Exports 0%"
    ZERO_RATED_LPO = "C2", "Zero-rated local purchase order 0%"
    ZERO_RATED = "C3", "Zero-rated by nature 0%"
    EXEMPT = "D", "Exempt, no tax charge"
    TURNOVER_TAX = "TOT", "Turnover tax, no VAT charge"


TAX_RATES = {
    TaxCategory.STANDARD: Decimal("16"),
    TaxCategory.MINIMUM_TAXABLE_VALUE: Decimal("16"),
    TaxCategory.EXPORTS: Decimal("0"),
    TaxCategory.ZERO_RATED_LPO: Decimal("0"),
    TaxCategory.ZERO_RATED: Decimal("0"),
    TaxCategory.EXEMPT: Decimal("0"),
    TaxCategory.TURNOVER_TAX: Decimal("0"),
}

# Payload key suffix for each category's taxblAmt*/taxRt*/taxAmt* totals.
PAYLOAD_SUFFIX = {
    TaxCategory.STANDARD: "A",
    TaxCategory.MINIMUM_TAXABLE_VALUE: "B",
    TaxCategory.EXPORTS: "C1",
    TaxCategory.ZERO_RATED_LPO: "C2",
    TaxCategory.ZERO_RATED: "C3",
    TaxCategory.EXEMPT: "D",
    TaxCategory.TURNOVER_TAX: "Tot",
}

SALES_TYPE_NORMAL = "N"  # 4.8 Transaction Type: only N is sent to ZRA.
RECEIPT_SALE = "S"  # 4.9 Sales Receipt Type
RECEIPT_REFUND = "R"
PAYMENT_CREDIT = "02"  # 4.10 Payment Method: invoiced now, paid later.
STATUS_APPROVED = "02"  # 4.11 Transaction Progress
REFUND_REASON_OTHER = "13"  # 4.16 Refund Reason Code
PRODUCT_TYPE_SERVICE = "3"  # 4.3 Product Type: service without stock
PACKAGING_NET = "NT"  # 4.5 Packaging Unit
QUANTITY_UNIT = "U"  # 4.6 Unit of Quantity

RESULT_OK = "000"
RESULT_NO_DATA = "001"
RESULT_INVALID_DEVICE = "902"
RESULT_ALREADY_INSTALLED = "903"
RESULT_PARAMETER_ERROR = "911"
