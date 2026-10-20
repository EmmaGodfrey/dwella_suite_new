"""Clients for the ZRA Virtual Sales Data Controller (VSDC).

The VSDC is a WAR file ZRA issues to each approved taxpayer; it runs on our
side and relays to Smart Invoice. Until Dwella has one, `FakeVsdcClient`
stands in: it checks requests the way the VSDC documentation describes and
answers in the same shape, so the real client can drop in behind
`ZRA_VSDC_CLIENT` without touching the billing code.
"""

import base64
import hashlib
import re
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string

from . import codes


class VsdcError(Exception):
    """The VSDC answered with a result code other than success."""

    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class FakeVsdcClient:
    TPIN = re.compile(r"\d{10}")
    SALE_FIELDS = (
        "tpin",
        "bhfId",
        "invcNo",
        "orgInvcNo",
        "salesTyCd",
        "rcptTyCd",
        "salesSttsCd",
        "cfmDt",
        "salesDt",
        "totItemCnt",
        "totTaxblAmt",
        "totTaxAmt",
        "totAmt",
        "prchrAcptcYn",
        "regrId",
        "regrNm",
        "modrId",
        "modrNm",
        "itemList",
    )
    ITEM_FIELDS = (
        "itemSeq", "itemCd", "itemClsCd", "itemNm", "pkgUnitCd", "pkg", "qtyUnitCd", "qty",
        "prc", "splyAmt", "dcRt", "dcAmt", "vatCatCd", "taxblAmt", "vatAmt", "totAmt",
    )  # fmt: skip

    def select_init_info(self, *, tpin, bhf_id, device_serial):
        self._check_branch(tpin, bhf_id)
        if not device_serial or len(device_serial) > 100:
            raise VsdcError(codes.RESULT_PARAMETER_ERROR, "Request parameter error")
        digest = self._digest(tpin, bhf_id, device_serial)
        return self._ok(
            {
                "info": {
                    "tpin": tpin,
                    "taxprNm": f"TAXPAYER {tpin}",
                    "bhfId": bhf_id,
                    "dvcId": digest[:20],
                    "sdcId": f"SDC0{tpin[-8:]}",
                    "mrcNo": f"WIS0{tpin[-7:]}",
                    "lastSaleInvcNo": 0,
                }
            }
        )

    def save_items(self, payload):
        self._check_branch(payload.get("tpin"), payload.get("bhfId"))
        missing = [
            key for key in ("itemCd", "itemClsCd", "itemNm", "vatCatCd") if not payload.get(key)
        ]
        if missing:
            raise VsdcError(codes.RESULT_PARAMETER_ERROR, f"Missing {', '.join(missing)}")
        return self._ok(None)

    def save_sales(self, payload):
        self._check_branch(payload.get("tpin"), payload.get("bhfId"))
        missing = [key for key in self.SALE_FIELDS if payload.get(key) is None]
        items = payload.get("itemList") or []
        for item in items:
            missing += [f"itemList.{key}" for key in self.ITEM_FIELDS if item.get(key) is None]
        if missing or not items:
            raise VsdcError(
                codes.RESULT_PARAMETER_ERROR, f"Missing {', '.join(missing) or 'items'}"
            )
        if payload["rcptTyCd"] == codes.RECEIPT_REFUND and not payload["orgInvcNo"]:
            raise VsdcError(codes.RESULT_PARAMETER_ERROR, "A refund needs orgInvcNo")
        if payload["totItemCnt"] != len(items):
            raise VsdcError(codes.RESULT_PARAMETER_ERROR, "totItemCnt does not match itemList")
        for total, part in (("totAmt", "totAmt"), ("totTaxAmt", "vatAmt")):
            if Decimal(str(payload[total])) != sum(Decimal(str(i[part])) for i in items):
                raise VsdcError(codes.RESULT_PARAMETER_ERROR, f"{total} does not add up")
        digest = self._digest(
            payload["tpin"], payload["bhfId"], payload["invcNo"], payload["totAmt"]
        )
        return self._ok(
            {
                "rcptNo": payload["invcNo"],
                "intrlData": digest[:26],
                "rcptSign": digest[26:42],
                "totRcptNo": payload["invcNo"],
                "vsdcRcptPbctDate": timezone.localtime().strftime("%Y%m%d%H%M%S"),
                "sdcId": f"SDC0{payload['tpin'][-8:]}",
                "mrcNo": f"WIS0{payload['tpin'][-7:]}",
            }
        )

    def _check_branch(self, tpin, bhf_id):
        if not tpin or not self.TPIN.fullmatch(str(tpin)) or not bhf_id or len(bhf_id) != 3:
            raise VsdcError(codes.RESULT_INVALID_DEVICE, "It is not valid device")

    @staticmethod
    def _digest(*parts):
        raw = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
        return base64.b32encode(raw).decode().rstrip("=")

    @staticmethod
    def _ok(data):
        return {
            "resultCd": codes.RESULT_OK,
            "resultMsg": "It is succeeded",
            "resultDt": timezone.localtime().strftime("%Y%m%d%H%M%S"),
            "data": data,
        }


def get_vsdc_client():
    return import_string(settings.ZRA_VSDC_CLIENT)()
