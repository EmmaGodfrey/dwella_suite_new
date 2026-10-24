"""A4 PDFs generated without fetching remote assets or accepting HTML."""

import hashlib
import io
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#1d417e")
INK = colors.HexColor("#111a2b")
MUTED = colors.HexColor("#4b566c")
LINE = colors.HexColor("#e7ebf2")
WASH = colors.HexColor("#f3f5f9")
WIDTH = A4[0] - 72


@lru_cache(maxsize=1)
def styles():
    fonts = Path(__file__).with_name("fonts")
    for name, file in [
        ("Figtree", "Figtree-400.ttf"),
        ("FigtreeBold", "Figtree-600.ttf"),
        ("Montserrat", "Montserrat-600.ttf"),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
    return {
        "body": ParagraphStyle(
            "body", fontName="Figtree", fontSize=10, leading=15, textColor=INK, spaceAfter=8
        ),
        "muted": ParagraphStyle(
            "muted", fontName="Figtree", fontSize=10, leading=15, textColor=MUTED, spaceAfter=8
        ),
        "small": ParagraphStyle(
            "small", fontName="Figtree", fontSize=8, leading=12, textColor=MUTED, spaceAfter=5
        ),
        "strong": ParagraphStyle(
            "strong", fontName="FigtreeBold", fontSize=10, leading=15, textColor=INK, spaceAfter=8
        ),
        "heading": ParagraphStyle(
            "heading",
            fontName="FigtreeBold",
            fontSize=12,
            leading=17,
            textColor=INK,
            spaceBefore=12,
            spaceAfter=9,
        ),
        "title": ParagraphStyle(
            "title", fontName="Montserrat", fontSize=21, leading=28, textColor=NAVY, spaceAfter=12
        ),
        "balance": ParagraphStyle(
            "balance",
            fontName="Montserrat",
            fontSize=20,
            leading=27,
            textColor=NAVY,
            alignment=TA_RIGHT,
        ),
    }


def p(value, style="body"):
    return Paragraph(escape(str(value or "")).replace("\n", "<br/>"), styles()[style])


def rule():
    return HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=10, spaceAfter=16)


def table(rows, widths, *, headings=False):
    result = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1 if headings else 0)
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]
    if headings:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), WASH),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
        ]
    result.setStyle(TableStyle(commands))
    return result


class NumberedCanvas(Canvas):
    def __init__(self, *args, footer="", **kwargs):
        super().__init__(*args, **kwargs)
        self.saved_pages = []
        self.footer = footer
        self.page_count = 0

    def showPage(self):  # noqa: N802
        self.saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        pages = len(self.saved_pages)
        for state in self.saved_pages:
            self.__dict__.update(state)
            self.setStrokeColor(LINE)
            self.line(36, 38, A4[0] - 36, 38)
            self.setFont("Figtree", 8)
            self.setFillColor(MUTED)
            self.drawString(36, 25, self.footer)
            self.drawRightString(A4[0] - 36, 25, f"Page {self._pageNumber} of {pages}")
            super().showPage()
        self.page_count = pages
        super().save()


def build(flow, reference):
    output = io.BytesIO()
    captured = []

    def canvas(*args, **kwargs):
        result = NumberedCanvas(*args, footer=reference, **kwargs)
        captured.append(result)
        return result

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=40,
        bottomMargin=58,
        title=reference,
        author="Dwella",
        pageCompression=1,
    )
    doc.build(flow, canvasmaker=canvas)
    return output.getvalue(), captured[0].page_count


def money(snapshot, amount):
    return f"{snapshot['issuer']['currency']} {Decimal(str(amount)):,.2f}"


def display_date(value, *, period=False):
    try:
        return date.fromisoformat(value).strftime("%B %Y" if period else "%d %B %Y")
    except (ValueError, TypeError):
        return str(value)


def invoice_pdf(s):
    issuer = s["issuer"]
    flow = [
        table(
            [
                [
                    [
                        p(issuer["name"], "heading"),
                        p(issuer["address"], "small"),
                        p(
                            " · ".join(filter(None, [issuer["email"], issuer["phone_number"]])),
                            "small",
                        ),
                    ],
                    [p("INVOICE", "title"), p(s["reference"], "strong"), p(s["status"], "small")],
                ]
            ],
            [WIDTH * 0.6, WIDTH * 0.4],
        ),
        rule(),
    ]
    flow += [
        table(
            [
                [
                    [p("Issue date", "small"), p(display_date(s["issue_date"]), "strong")],
                    [p("Due date", "small"), p(display_date(s["due_date"]), "strong")],
                    [
                        p("Billing period", "small"),
                        p(display_date(s["period"], period=True), "strong"),
                    ],
                ]
            ],
            [WIDTH / 3] * 3,
        ),
        Spacer(1, 10),
    ]
    flow += [
        table(
            [
                [
                    [
                        p("BILL TO", "small"),
                        p(s["tenant_name"], "strong"),
                        p(s["tenant_email"], "muted"),
                        p(s["tenant_phone"], "muted"),
                    ],
                    [
                        p("PROPERTY / UNIT", "small"),
                        p(s["premises"], "strong"),
                        p(s["property_address"], "muted"),
                        p(s["lease_reference"], "muted"),
                    ],
                ]
            ],
            [WIDTH / 2] * 2,
        ),
        Spacer(1, 16),
    ]
    rows = [[p("Description", "small"), p("Type", "small"), p("Amount", "small")]]
    rows += [
        [p(line["description"]), p(line["kind"], "muted"), p(money(s, line["amount"]), "strong")]
        for line in s["lines"]
    ]
    flow += [table(rows, [WIDTH * 0.54, WIDTH * 0.18, WIDTH * 0.28], headings=True), Spacer(1, 18)]
    payments = [p("Payments received", "strong")]
    payments += [
        p(
            f"{pay['receipt']} · {pay['date']}\n{pay['method']} · " f"{money(s, pay['amount'])}",
            "small",
        )
        for pay in s["payments"]
    ]
    if len(payments) == 1:
        payments.append(p("No payments recorded.", "muted"))
    totals = [
        p(f"Invoice total: {money(s, s['total'])}"),
        p(f"Paid to date: {money(s, s['amount_paid'])}"),
        rule(),
        p("Balance due", "small"),
        p(money(s, s["balance"]), "balance"),
    ]
    if len(s["payments"]) > 6:
        payment_rows = [[p(label, "small") for label in ["Receipt", "Date", "Method", "Amount"]]]
        payment_rows += [
            [
                p(pay["receipt"]),
                p(display_date(pay["date"])),
                p(pay["method"]),
                p(money(s, pay["amount"]), "strong"),
            ]
            for pay in s["payments"]
        ]
        flow += [
            p("Payments received", "heading"),
            table(
                payment_rows,
                [WIDTH * 0.23, WIDTH * 0.25, WIDTH * 0.24, WIDTH * 0.28],
                headings=True,
            ),
            Spacer(1, 16),
        ]
        payments = [p("All recorded payments are listed above.", "muted")]
    flow += [
        table([[payments, totals]], [WIDTH * 0.54, WIDTH * 0.46]),
        rule(),
        p("Payment instructions", "heading"),
        p(
            f"Use the payment details provided by your property manager. Quote {s['reference']} "
            "so the payment can be matched to this invoice.",
            "muted",
        ),
    ]
    if s.get("tax_reference"):
        flow += [p(f"Issuer TPIN: {s['tax_reference']}", "small")]
    # Internal invoice notes are deliberately not part of the recipient document.
    return build(flow, f"Issued via Dwella · {s['reference']} · Snapshot v{s['version']}")


def lease_pdf(s, signatures=()):
    flow = [
        p(s["issuer"]["name"], "strong"),
        p("Residential tenancy agreement", "title"),
        p(f"{s['reference']} · Version {s['version']} · Prepared {s['prepared_on']}", "small"),
        rule(),
        p("Parties", "heading"),
        table(
            [
                [
                    [
                        p("Landlord", "small"),
                        p(s["landlord_name"], "strong"),
                        p(s["landlord_address"], "muted"),
                    ],
                    [
                        p("Tenant", "small"),
                        p(s["tenant_name"], "strong"),
                        p(s["tenant_email"], "muted"),
                        p(s["tenant_phone"], "muted"),
                    ],
                ]
            ],
            [WIDTH / 2] * 2,
        ),
        p("Premises", "heading"),
        p(s["premises"], "strong"),
        p(s["property_address"], "muted"),
        p("Terms at a glance", "heading"),
    ]
    terms = [
        ("Lease period", f"{display_date(s['start_date'])} – {display_date(s['end_date'])}"),
        ("Monthly rent", money(s, s["monthly_rent"])),
        ("Rent due", f"Day {s['rent_due_day']} of each month"),
        ("Security deposit", money(s, s["deposit_amount"])),
        ("Notice period", f"{s['notice_period_months']} month(s)"),
        (
            "Late fee",
            f"{s['late_fee_percent']}% after {s['late_fee_grace_days']} days"
            if float(s["late_fee_percent"])
            else "None",
        ),
    ]
    flow += [
        table(
            [[p(label, "muted"), p(value, "strong")] for label, value in terms],
            [WIDTH * 0.4, WIDTH * 0.6],
        ),
        p("Agreement terms", "heading"),
    ]
    # Plain text only; never let tenant/manager content become ReportLab markup.
    for paragraph in s["agreement_text"].split("\n\n"):
        flow += [p(paragraph)]
    if s.get("schedule_text"):
        flow += [p("Schedules and additional terms", "heading")]
        flow += [p(part) for part in s["schedule_text"].split("\n\n")]
    flow += [
        PageBreak(),
        p("Execution and signatures", "title"),
        p(f"{s['reference']} · Version {s['version']}", "small"),
        rule(),
        p(
            "Each signature applies to this complete agreement, its terms and listed schedules.",
            "muted",
        ),
    ]
    for role, name in [("landlord", s["landlord_signer_name"]), ("tenant", s["tenant_name"])]:
        signature = next((item for item in signatures if item.role == role), None)
        block = [p("For the landlord" if role == "landlord" else "Tenant", "heading")]
        if signature:
            image = Image(io.BytesIO(bytes(signature.png)))
            image._restrictSize(WIDTH - 40, 64)
            image.hAlign = "LEFT"
            block += [image, Spacer(1, 10)]
        else:
            block += [p("Awaiting signature", "muted"), Spacer(1, 50)]
        block += [p(name, "strong")]
        if role == "landlord":
            block += [p(f"Authorised signatory for {s['landlord_name']}", "small")]
        block += [
            p(
                signature.signed_at.strftime("Signed %d %B %Y at %H:%M UTC")
                if signature
                else "Date: pending",
                "small",
            ),
            rule(),
        ]
        flow.append(KeepTogether(block))
    flow += [
        p("Electronic signing record", "heading"),
        p("This records electronic signatures, not certificate-based digital signatures.", "small"),
    ]
    for signature in signatures:
        flow += [
            p(f"{signature.signer_name} · {signature.role}", "strong"),
            p(
                f"Authentication: {signature.authentication_method} · "
                f"Signed: {signature.signed_at.strftime('%d %B %Y at %H:%M UTC')}",
                "small",
            ),
            p(f"Reviewed document SHA-256: {signature.reviewed_sha256}", "small"),
            p(signature.consent, "small"),
        ]
    if not signatures:
        flow.append(p("No signatures have been recorded.", "small"))
    return build(flow, f"{s['reference']} · Version {s['version']} · Generated via Dwella")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()
