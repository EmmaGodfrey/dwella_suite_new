import re

ZAMBIA_CODE = "260"


def normalize_phone_number(value):
    """Return `value` as E.164, reading local numbers as Zambian.

    Accepts `0971234567`, `971234567`, `260971234567` and `+260 97 123 4567`
    style input, plus any other `+<country><number>`. Returns None when the
    result is not a plausible phone number.
    """
    raw = (value or "").strip()
    has_plus = raw.startswith("+") or raw.startswith("00")
    digits = re.sub(r"\D", "", raw)
    if raw.startswith("00"):
        digits = digits[2:]

    if not has_plus:
        if digits.startswith("0") and len(digits) == 10:
            digits = ZAMBIA_CODE + digits[1:]
        elif len(digits) == 9:
            digits = ZAMBIA_CODE + digits

    if digits.startswith(ZAMBIA_CODE):
        return f"+{digits}" if len(digits) == 12 else None
    if has_plus and 8 <= len(digits) <= 15:
        return f"+{digits}"
    return None
