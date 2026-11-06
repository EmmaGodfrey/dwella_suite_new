"""Build the tester pack from reviewed source; adds no application dependencies.

Run --office with python-docx/openpyxl, --pdf with the backend's ReportLab.
Generated files stay in ignored output/alpha-test; no tester data is embedded.
"""
import argparse
import itertools
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output/alpha-test"
SOURCE = ROOT / "docs/ALPHA_UAT_2026_11_07.md"
CASES = json.loads(Path(__file__).with_name("alpha_cases.json").read_text(encoding="utf-8"))
LOGO = ROOT / "frontend/public/assets/images/logo/dwella-lockup.png"
STEM = "Dwella_Alpha_Tester_Handbook_2026-11-07"
NAVY, GREEN, MUTED = "0B1930", "197142", "516174"
assert len(CASES) == len({row[0] for row in CASES})


def sections():
    for title, items in itertools.groupby(CASES, key=lambda row: row[1]):
        yield title, list(items)


def lines():
    return SOURCE.read_text(encoding="utf-8").splitlines()


def office():
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor
    from openpyxl import Workbook
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.worksheet.table import Table, TableStyleInfo

    doc = Document()
    doc.core_properties.title = "Dwella Suite Alpha Tester Handbook"
    doc.core_properties.author = "Dwella Suite"
    doc.core_properties.subject = "User acceptance testing in the existing TEST application"
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.27), Inches(11.69)
    section.top_margin = section.bottom_margin = Inches(.65)
    section.left_margin = section.right_margin = Inches(.7)
    base = doc.styles["Normal"]
    base.font.name, base.font.size = "Calibri", Pt(10)
    base.font.color.rgb = RGBColor.from_string(NAVY)
    base.paragraph_format.space_after = Pt(6)
    for style in ["Title", "Heading 1", "Heading 2", "Heading 3"]:
        doc.styles[style].font.name = "Calibri"
        doc.styles[style].font.color.rgb = RGBColor.from_string(
            GREEN if style == "Heading 3" else NAVY,
        )
    header = section.header.paragraphs[0]
    header.text = "DWELLA SUITE  /  TESTER HANDBOOK"
    header.runs[0].font.size = Pt(8)
    header.runs[0].font.color.rgb = RGBColor.from_string(MUTED)
    footer = section.footer.paragraphs[0]
    footer.text = "External alpha · Existing TEST environment · 7 November 2026     |     "
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    for run in footer.runs:
        run.font.size = Pt(8)
    doc.add_picture(str(LOGO), width=Inches(2.15))
    doc.add_paragraph("ALPHA TEST · VERSION 1.0", "Subtitle")
    doc.add_heading("Help shape\na better Dwella", 0)
    doc.add_paragraph("Tester handbook, acceptance cases and feedback guide")
    doc.add_paragraph("7 November 2026\nhttps://app.dwella.properties/test/")
    doc.add_heading("Real people. Complete journeys. Useful feedback.", 2)
    doc.add_paragraph(
        "Use Dwella as a manager or tenant, note what works, and tell us where the "
        "experience breaks down. This pack contains 120 role-based cases; the organiser "
        "assigns the cases relevant to you.",
    )
    doc.add_paragraph("Use test tenancy data. Online money movement is disabled.")
    doc.add_page_break()
    for line in lines():
        if not line or line.startswith("# "):
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:], 1)
        elif line.startswith("- "):
            doc.add_paragraph(line[2:], "List Bullet")
        else:
            doc.add_paragraph(line)
    doc.add_page_break()
    doc.add_heading("Acceptance case catalogue", 0)
    doc.add_paragraph(
        "Complete your assigned cases in the results workbook. The lines below may "
        "also be used for printed notes. No case has been pre-marked as passed.",
    )
    for title, rows in sections():
        doc.add_heading(title, 1)
        for identity, _, role, priority, name, steps, expected in rows:
            doc.add_heading(f"{identity}  ·  {name}", 2)
            meta = doc.add_paragraph(f"{priority}  |  {role}")
            meta.paragraph_format.keep_with_next = True
            for label, text in [("Steps", steps), ("Expected", expected)]:
                paragraph = doc.add_paragraph()
                paragraph.add_run(label + ": ").bold = True
                paragraph.add_run(text)
            result = doc.add_paragraph(
                "Result: Not run / Pass / Fail / Blocked / N/A\n"
                "Actual result / evidence: __________________________________________",
            )
            result.paragraph_format.space_after = Pt(12)
    doc.save(OUT / (STEM + ".docx"))

    book = Workbook()
    summary = book.active
    summary.title = "Start here"
    summary.append(["DWELLA SUITE · ALPHA RESULTS"])
    summary.merge_cells("A1:B1")
    summary.append(["Environment", "https://app.dwella.properties/test/"])
    summary.append(["Pack date", "7 November 2026"])
    summary.append(["Tester / team", ""])
    summary.append(["Assigned role(s)", ""])
    summary.append(["Release / build", ""])
    summary.append(["Test window", ""])
    summary.append(["Instructions", "Filter Cases by your role. Run P0 first; record actual results and evidence. Use Bugs for failures."])
    summary.append(["Boundary", "No real payments. Use consenting participants' own inboxes/phones and fictional tenancy data."])
    summary.append([])
    summary.append(["Status", "Count"])
    sheet = book.create_sheet("Cases")
    headers = ["Case ID", "Module", "Role", "Priority", "Test case", "Steps", "Expected result",
               "Status", "Tester", "Device / browser", "Release / build", "Actual result",
               "Evidence link", "Bug ID", "Checked date", "Retest notes"]
    sheet.append(headers)
    for identity, module, role, priority, title, steps, expected in CASES:
        sheet.append([identity, module, role, priority, title, steps, expected,
                      "Not run", "", "", "", "", "", "", "", ""])
    end = len(CASES) + 1
    status = DataValidation(type="list", formula1='"Not run,Pass,Fail,Blocked,Not applicable"')
    sheet.add_data_validation(status)
    status.add(f"H2:H{end}")
    status.errorTitle, status.error = "Choose a status", "Use one of the listed execution statuses."
    status.showErrorMessage = True
    table = Table(displayName="AlphaCases", ref=f"A1:P{end}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    sheet.add_table(table)
    widths = [15, 25, 24, 10, 38, 80, 80, 19, 22, 25, 20, 70, 45, 18, 20, 60]
    from openpyxl.utils import get_column_letter
    for col, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(col)].width = width
    sheet.freeze_panes = "B2"
    sheet.sheet_view.zoomScale = 85
    sheet.print_title_rows = "1:1"
    sheet.page_setup.orientation = "landscape"
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        sheet.row_dimensions[row[0].row].height = 78
    for word, colour in [("Pass", "E5F4EA"), ("Fail", "FCE8E6"), ("Blocked", "FFF3CD")]:
        sheet.conditional_formatting.add(f"H2:H{end}", CellIsRule(
            operator="equal", formula=[f'"{word}"'], fill=PatternFill("solid", fgColor=colour),
        ))
    for index, word in enumerate(["Not run", "Pass", "Fail", "Blocked", "Not applicable"], 12):
        summary.cell(index, 1, word)
        summary.cell(index, 2, f'=COUNTIF(Cases!H2:H{end},A{index})')
    summary.cell(18, 1, "Total cases")
    summary.cell(18, 2, len(CASES))
    summary.cell(20, 1, "Feedback")
    summary.cell(20, 2, "What was confusing? What blocked you? Which three changes matter most?")
    summary.column_dimensions["A"].width = 26
    summary.column_dimensions["B"].width = 100
    for row in summary:
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    bugs = book.create_sheet("Bugs")
    bugs.append(["Bug ID", "Case ID", "Module", "Role", "Title", "Severity", "Steps to reproduce",
                 "Expected", "Actual", "Device / browser", "Build", "Date / time", "Evidence link",
                 "Reproducibility", "Owner", "Status", "Fix build", "Retest result"])
    for index in range(1, 26):
        bugs.append([f"BUG-{index:03}"] + [""] * 17)
    bugs.freeze_panes = "B2"
    bugs.auto_filter.ref = "A1:R26"
    for col in range(1, 19):
        bugs.column_dimensions[get_column_letter(col)].width = 24 if col < 7 else 48
    for col, options in [("F", '"Critical,High,Medium,Low"'),
                         ("P", '"New,Triaged,In progress,Ready for retest,Closed,Deferred"')]:
        rule = DataValidation(type="list", formula1=options)
        bugs.add_data_validation(rule)
        rule.add(f"{col}2:{col}1000")
    for ws in book:
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        for cell in ws[1]:
            cell.fill = PatternFill("solid", fgColor=NAVY)
            cell.font = Font(name="Calibri", bold=True, color="FFFFFF")
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        ws.row_dimensions[1].height = 30
        ws.oddFooter.center.text = "Dwella Suite · Alpha test · Page &P of &N"
    book.save(OUT / "Dwella_Alpha_Results_2026-11-07.xlsx")


def pdf():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
    )

    regular = Path("C:/Windows/Fonts/arial.ttf")
    bold = Path("C:/Windows/Fonts/arialbd.ttf")
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("Dwella", str(regular)))
        pdfmetrics.registerFont(TTFont("DwellaBold", str(bold)))
        pdfmetrics.registerFontFamily("Dwella", normal="Dwella", bold="DwellaBold")
        font, strong = "Dwella", "DwellaBold"
    else:
        font, strong = "Helvetica", "Helvetica-Bold"
    navy, green, muted = [colors.HexColor("#" + value) for value in [NAVY, GREEN, MUTED]]
    styles = getSampleStyleSheet()
    for key in ["BodyText", "Normal", "Bullet"]:
        styles[key].fontName = font
        styles[key].fontSize, styles[key].leading = 10, 14
        styles[key].textColor = navy
        styles[key].spaceAfter = 8
    for key, size in [("Title", 31), ("Heading1", 19), ("Heading2", 14), ("Heading3", 11)]:
        styles[key].fontName, styles[key].fontSize = strong, size
        styles[key].leading = size + 5
        styles[key].textColor = green if key == "Heading3" else navy
        styles[key].spaceBefore, styles[key].spaceAfter = 14, 9
        styles[key].alignment = TA_LEFT
    styles.add(ParagraphStyle("Meta", fontName=font, fontSize=8.5, leading=12,
                             textColor=muted, spaceAfter=7))
    styles.add(ParagraphStyle("Case", parent=styles["BodyText"], fontSize=9.5, leading=13))
    story = []
    def p(text, style="BodyText"):
        return Paragraph(escape(text).replace("\n", "<br/>"), styles[style])
    logo = Image(str(LOGO), width=174, height=43, kind="proportional", hAlign="LEFT")
    story += [Spacer(1, 30), logo, Spacer(1, 52), p("ALPHA TEST · VERSION 1.0", "Meta"),
              p("Help shape\na better Dwella", "Title"), Spacer(1, 14),
              p("Tester handbook, acceptance cases\nand feedback guide", "Heading2"),
              Spacer(1, 28), p("7 November 2026", "Meta"),
              p("https://app.dwella.properties/test/"), Spacer(1, 36),
              p("Real people. Complete journeys. Useful feedback.", "Heading2"),
              p("Use Dwella as a manager or tenant and tell us where the experience breaks down. "
                "This pack contains 120 role-based cases; the organiser assigns the cases relevant to you."),
              p("Use test tenancy data. Online money movement is disabled.", "Meta"), PageBreak()]
    for line in lines():
        if not line or line.startswith("# "):
            continue
        if line.startswith("## "):
            story.append(p(line[3:], "Heading1"))
        elif line.startswith("- "):
            story.append(Paragraph(escape(line[2:]), styles["Bullet"], bulletText="•"))
        else:
            story.append(p(line))
    story += [PageBreak(), p("Acceptance case catalogue", "Title"),
              p("Run assigned P0 cases first. Record results in the workbook; use the lines below "
                "for printed notes. No case has been pre-marked as passed.")]
    for title, rows in sections():
        story.append(p(title, "Heading1"))
        for identity, _, role, priority, name, steps, expected in rows:
            block = [p(f"{identity} · {name}", "Heading3"), p(f"{priority}  |  {role}", "Meta")]
            block.append(Paragraph("<b>Steps:</b> " + escape(steps), styles["Case"]))
            block.append(Paragraph("<b>Expected:</b> " + escape(expected), styles["Case"]))
            block += [p("Result: Not run / Pass / Fail / Blocked / N/A", "Meta"),
                      p("Actual result / evidence: ______________________________________________", "Meta"),
                      Spacer(1, 6)]
            story.append(KeepTogether(block))
    def page(canvas, doc):
        width, height = A4
        canvas.setStrokeColor(green)
        canvas.setLineWidth(2)
        canvas.line(43, height - 29, width - 43, height - 29)
        canvas.setFont(font, 7.5)
        canvas.setFillColor(muted)
        canvas.drawString(43, 26, "DWELLA SUITE  /  ALPHA TEST  /  7 NOVEMBER 2026")
        canvas.drawRightString(width - 43, 26, str(doc.page))
    SimpleDocTemplate(
        str(OUT / (STEM + ".pdf")), pagesize=A4, rightMargin=43, leftMargin=43,
        topMargin=43, bottomMargin=46, title="Dwella Suite Alpha Tester Handbook",
        author="Dwella Suite", subject="Role-based user acceptance testing in TEST",
    ).build(story, onFirstPage=page, onLaterPages=page)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--office", action="store_true")
    parser.add_argument("--pdf", action="store_true")
    options = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if options.office:
        office()
    if options.pdf:
        pdf()
    print(f"Built tester pack: {len(CASES)} cases; output/alpha-test")
