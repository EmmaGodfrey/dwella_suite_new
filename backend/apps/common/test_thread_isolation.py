from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace

import pytest

from apps.documents.rendering import invoice_pdf, styles
from apps.notifications.actor_context import NoticeActorMiddleware, current_actor


def test_notice_actor_is_isolated_and_reset_across_reused_threads():
    barrier = Barrier(8)

    def handle(request):
        # Authentication happens inside DRF after middleware has set the request.
        request.user = SimpleNamespace(pk=request.expected, is_authenticated=True)
        barrier.wait(timeout=10)
        assert current_actor().pk == request.expected
        if request.expected % 2:
            raise ValueError("simulated view failure")
        return current_actor().pk

    middleware = NoticeActorMiddleware(handle)

    def invoke(number):
        assert current_actor() is None
        request = SimpleNamespace(expected=number)
        if number % 2:
            with pytest.raises(ValueError):
                middleware(request)
        else:
            assert middleware(request) == number
        assert current_actor() is None

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(invoke, range(32)))
    assert current_actor() is None


def invoice_snapshot(marker):
    return {
        "issuer": {
            "name": marker,
            "address": "Synthetic test address",
            "email": "test@example.com",
            "phone_number": "+260971000000",
            "currency": "ZMW",
        },
        "reference": marker,
        "status": "issued",
        "issue_date": "2026-11-01",
        "due_date": "2026-11-05",
        "period": "2026-11-01",
        "tenant_name": marker,
        "tenant_email": "tenant@example.com",
        "tenant_phone": "+260971000001",
        "premises": "Synthetic unit",
        "property_address": "Test address",
        "lease_reference": "Synthetic lease",
        "lines": [
            {"description": marker, "kind": "rent", "amount": "100.00"},
        ],
        "payments": [],
        "total": "100.00",
        "amount_paid": "0.00",
        "balance": "100.00",
        "version": 1,
    }


def test_concurrent_reportlab_documents_do_not_mix_content():
    import pypdfium2 as pdfium

    styles.cache_clear()
    barrier = Barrier(8)
    markers = [f"THREAD{number:03}" for number in range(24)]

    def render(marker):
        barrier.wait(timeout=10)
        return invoice_pdf(invoice_snapshot(marker))

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(render, markers))
    # PDFium itself is not thread safe: extract sequentially after rendering ends.
    for marker, (raw, pages) in zip(markers, results, strict=True):
        assert raw.startswith(b"%PDF-") and pages >= 1
        with pdfium.PdfDocument(raw) as pdf:
            text = ""
            for index in range(len(pdf)):
                page = pdf[index]
                try:
                    textpage = page.get_textpage()
                    try:
                        text += textpage.get_text_range()
                    finally:
                        textpage.close()
                finally:
                    page.close()
        assert marker in text
        assert all(other not in text for other in markers if other != marker)
