"""Small bounded XLSX reader; no formulas, links, macros or extra worksheets.

Only cell values are needed for this import, so use the standard ZIP/XML
libraries rather than loading an Excel workbook engine or evaluating content.
"""

import csv
import re
from datetime import date, timedelta
from io import BytesIO, StringIO
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from rest_framework.exceptions import ValidationError

MAX_BYTES = 1_000_000
MAX_XML = 8_000_000
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
IDENTITY = {
    "phone",
    "phone_number",
    "national_id",
    "nrc",
    "tpin",
    "company_registration",
    "representative_phone",
}
DATES = {"lease_start", "lease_end", "start_date", "end_date"}


def uploaded_csv(upload):
    raw = upload.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValidationError("Choose a file no larger than 1 MB.")
    if upload.name.lower().endswith(".csv"):
        try:
            return raw.decode("utf-8-sig")
        except UnicodeError as error:
            raise ValidationError("Save the CSV using UTF-8 encoding.") from error
    if not upload.name.lower().endswith(".xlsx"):
        raise ValidationError("Choose a CSV or XLSX file.")
    try:
        return xlsx_csv(raw)
    except (
        BadZipFile,
        ET.ParseError,
        KeyError,
        ValueError,
        OverflowError,
        IndexError,
        AttributeError,
        RuntimeError,
    ) as error:
        raise ValidationError(
            "This Excel file could not be read. Use the template and one worksheet."
        ) from error


def xlsx_csv(raw):
    with ZipFile(BytesIO(raw)) as book:
        entries = book.infolist()
        if len(entries) > 100 or sum(item.file_size for item in entries) > MAX_XML:
            raise ValidationError("This Excel file expands beyond the import limit.")
        if len({item.filename for item in entries}) != len(entries):
            raise ValidationError("The Excel file has duplicate archive entries.")
        if any(
            "externallinks/" in item.filename.lower() or "vbaproject" in item.filename.lower()
            for item in entries
        ):
            raise ValidationError("Remove external links and macros before importing.")

        def xml(path):
            content = book.read(path)
            if b"\x00" in content:
                raise ValidationError("Use UTF-8 XML parts in the Excel file.")
            if len(re.findall(rb"<(?![/!?])", content)) > 100_000:
                raise ValidationError("This Excel file has too many XML elements for an import.")
            if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
                raise ValidationError("This Excel file contains unsupported XML declarations.")
            return ET.fromstring(content)

        sheets = [
            item.filename
            for item in entries
            if re.fullmatch(r"xl/worksheets/[^/]+\.xml", item.filename)
        ]
        if len(sheets) != 1:
            raise ValidationError("Keep exactly one worksheet in the import file.")
        strings = []
        if "xl/sharedStrings.xml" in book.namelist():
            strings = [
                "".join(item.itertext()) for item in xml("xl/sharedStrings.xml").findall("s:si", NS)
            ]
        properties = xml("xl/workbook.xml").find("s:workbookPr", NS)
        epoch = (
            date(1904, 1, 1)
            if properties is not None and properties.get("date1904") in {"1", "true"}
            else date(1899, 12, 30)
        )
        table, headers = [], []
        for row in xml(sheets[0]).findall("s:sheetData/s:row", NS):
            if len(table) >= 501:
                raise ValidationError("Import at most 500 rows at a time.")
            cells = {}
            for cell in row.findall("s:c", NS):
                if cell.find("s:f", NS) is not None:
                    raise ValidationError(
                        "Replace spreadsheet formulas with their values before importing."
                    )
                match = re.fullmatch(r"([A-Z]{1,3})\d+", cell.get("r", ""))
                if not match:
                    raise ValidationError("The worksheet contains an invalid cell address.")
                col = 0
                for letter in match[1]:
                    col = col * 26 + ord(letter) - 64
                if col > 60:
                    raise ValidationError("Use at most 60 import columns.")
                kind = cell.get("t")
                value = cell.findtext("s:v", default="", namespaces=NS)
                if kind == "s":
                    index = int(value)
                    if not 0 <= index < len(strings):
                        raise ValidationError("The worksheet contains an invalid text reference.")
                    value = strings[index]
                elif kind == "inlineStr":
                    value = "".join(cell.find("s:is", NS).itertext())
                elif kind in {"e", "b"}:
                    raise ValidationError("Remove spreadsheet errors and boolean cells.")
                if len(value) > 2000:
                    raise ValidationError("An import cell exceeds 2,000 characters.")
                if (
                    table
                    and col <= len(headers)
                    and value
                    and kind not in {"s", "inlineStr", "str", "d"}
                ):
                    if headers[col - 1] in IDENTITY:
                        raise ValidationError(
                            "Format phone and identity columns as Text to preserve leading zeros."
                        )
                    if headers[col - 1] in DATES:
                        if not value.isdigit():
                            raise ValidationError("Use dates without a time in lease date columns.")
                        value = (epoch + timedelta(days=int(value))).isoformat()
                if col in cells:
                    raise ValidationError("The worksheet contains duplicate cell addresses.")
                cells[col] = value
            if not any(cells.values()):
                continue
            values = [cells.get(col, "") for col in range(1, max(cells, default=0) + 1)]
            if not table:
                headers = [value.strip().lower().replace(" ", "_") for value in values]
            table.append(values)
        out = StringIO()
        csv.writer(out).writerows(table)
        return out.getvalue()
