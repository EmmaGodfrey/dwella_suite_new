"""Bulk CSV imports: template, preview, then a one-time confirmation.

The preview validates every row and returns a signed token holding the rows
that are ready. Confirming re-checks those rows inside one transaction, under
the workspace's record-limit lock, and creates all of them or none: if anything
changed since the preview, the manager previews again.
"""

import csv
import json
from hashlib import sha256
from io import StringIO

from django.core import signing
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.audit.services import record_event
from apps.subscriptions.services import capacity_guard

from .models import PortfolioImport

MAX_ROWS = 500
SALT = "portfolio.import.preview.v1"
PREVIEW_SECONDS = 30 * 60


class UploadSerializer(serializers.Serializer):
    csv = serializers.CharField(max_length=1_000_000, trim_whitespace=False)


class ConfirmSerializer(serializers.Serializer):
    preview_token = serializers.CharField(max_length=500_000)


def header(name):
    return "_".join((name or "").strip().lower().replace("-", " ").split())


class Importer:
    """One kind of record. Subclasses describe columns and how rows become records."""

    kind = ""
    resource = ""
    noun = ""
    # (column, required, example) in template order.
    columns = ()
    aliases = {}
    row_serializer = None

    def __init__(self, organization):
        self.organization = organization

    def clean(self, values):
        """Return (data, errors) for one row of raw strings."""
        serializer = self.row_serializer(data=values, context={"importer": self})
        if serializer.is_valid():
            return serializer.validated_data, None
        errors = serializer.errors
        return None, {key: [str(item) for item in value] for key, value in errors.items()}

    def key(self, data):
        raise NotImplementedError

    def existing(self, data):
        """A message when the record already exists in the workspace."""
        raise NotImplementedError

    def create(self, data):
        raise NotImplementedError

    def label(self, data):
        raise NotImplementedError


def template_response(importer):
    out = StringIO()
    writer = csv.writer(out)
    writer.writerow([column for column, _, _ in importer.columns])
    writer.writerow([example for _, _, example in importer.columns])
    response = HttpResponse(out.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="dwella-{importer.kind}-template.csv"'
    return response


def read_rows(importer, text):
    reader = csv.reader(StringIO(text.lstrip("﻿")), strict=True)
    try:
        raw_headers = next(reader, None)
        if not raw_headers:
            raise ValidationError("The file is empty. Start from the template.")
        known = {column for column, _, _ in importer.columns}
        headers = [importer.aliases.get(header(name), header(name)) for name in raw_headers]
        missing = [c for c, required, _ in importer.columns if required and c not in headers]
        if missing:
            plural = "s" if len(missing) > 1 else ""
            raise ValidationError({"columns": [f"Add the column{plural}: {', '.join(missing)}."]})
        rows = []
        for number, cells in enumerate(reader, 2):
            if not any(cell.strip() for cell in cells):
                continue
            if len(rows) >= MAX_ROWS:
                raise ValidationError(f"Import at most {MAX_ROWS} rows at a time.")
            values = {
                name: cell.strip()
                for name, cell in zip(headers, cells, strict=False)
                if name in known and cell.strip()
            }
            rows.append((number, values))
    except (csv.Error, UnicodeError) as error:
        raise ValidationError("The file could not be read. Save it as CSV (UTF-8).") from error
    if not rows:
        raise ValidationError(f"The file has no {importer.noun} rows.")
    ignored = sorted({name for name in headers if name and name not in known})
    return rows, ignored


def check(importer, rows):
    """Classify rows as ready, duplicate or invalid, in file order."""
    results, seen = [], {}
    for number, values in rows:
        data, errors = importer.clean(values)
        if errors:
            results.append({"row": number, "status": "invalid", "values": values, "errors": errors})
            continue
        key = importer.key(data)
        message = (
            f"Same as row {seen[key]} in this file." if key in seen else importer.existing(data)
        )
        seen.setdefault(key, number)
        results.append(
            {
                "row": number,
                "status": "duplicate" if message else "ready",
                "values": values,
                "label": importer.label(data),
                "message": message,
                "data": data,
            }
        )
    return results


def public(results):
    return [{k: v for k, v in item.items() if k != "data" and v is not None} for item in results]


def preview(importer, request, payload):
    upload = UploadSerializer(data=payload)
    upload.is_valid(raise_exception=True)
    rows, ignored = read_rows(importer, upload.validated_data["csv"])
    results = check(importer, rows)
    ready = [[item["row"], item["values"]] for item in results if item["status"] == "ready"]
    token = signing.dumps(
        {
            "o": str(importer.organization.public_id),
            "u": request.user.pk,
            "k": importer.kind,
            "rows": ready,
        },
        salt=SALT,
        compress=True,
    )
    counts = {
        status: sum(item["status"] == status for item in results)
        for status in ("ready", "duplicate", "invalid")
    }
    return {
        "rows": public(results),
        "counts": counts,
        "ignored_columns": ignored,
        "preview_token": token if ready else None,
    }


def confirm(importer, request, payload):
    form = ConfirmSerializer(data=payload)
    form.is_valid(raise_exception=True)
    token = form.validated_data["preview_token"]
    try:
        content = signing.loads(token, salt=SALT, max_age=PREVIEW_SECONDS)
    except signing.SignatureExpired as error:
        raise ValidationError("This preview has expired. Upload the file again.") from error
    except signing.BadSignature as error:
        raise ValidationError("This preview is not valid. Upload the file again.") from error
    if (
        content.get("o") != str(importer.organization.public_id)
        or content.get("u") != request.user.pk
        or content.get("k") != importer.kind
        or not content.get("rows")
    ):
        raise ValidationError("This preview is not valid. Upload the file again.")
    rows = [(number, values) for number, values in content["rows"]]
    digest = sha256(
        json.dumps([importer.organization.pk, importer.kind, rows], sort_keys=True).encode()
    ).hexdigest()
    with capacity_guard(importer.organization, importer.resource, additional=len(rows)):
        # The guard holds the workspace lock, so two imports cannot interleave.
        results = check(importer, rows)
        changed = [item for item in results if item["status"] != "ready"]
        if changed:
            raise ValidationError(
                {
                    "message": "Some rows changed since the preview. Upload the file again.",
                    "rows": public(changed),
                }
            )
        try:
            with transaction.atomic():
                receipt = PortfolioImport.objects.create(
                    organization=importer.organization,
                    kind=importer.kind,
                    digest=digest,
                    created_count=len(results),
                    created_by=request.user,
                )
        except IntegrityError as error:
            raise ValidationError("This preview was already imported.") from error
        created = [importer.create(item["data"]) for item in results]
        record_event(
            request,
            f"portfolio.{importer.kind}_imported",
            receipt,
            importer.organization,
            count=len(created),
        )
    return created
