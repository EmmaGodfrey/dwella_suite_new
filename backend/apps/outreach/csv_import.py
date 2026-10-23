import csv
from io import StringIO

from django.core import signing
from rest_framework import serializers

from .models import Contact, Suppression
from .serializers import ContactSerializer

SALT = "outreach.csv.preview.v1"


class ImportPreviewSerializer(serializers.Serializer):
    csv = serializers.CharField(max_length=1_000_000, trim_whitespace=False)
    mapping = serializers.DictField(child=serializers.CharField(max_length=150), required=False)


def preview_import(data):
    validator = ImportPreviewSerializer(data=data)
    validator.is_valid(raise_exception=True)
    reader = csv.DictReader(StringIO(validator.validated_data["csv"].lstrip("\ufeff")), strict=True)
    fields = {
        "name",
        "first_name",
        "salutation",
        "email",
        "phone",
        "whatsapp",
        "organization",
        "title",
        "segment",
        "platform",
        "handle",
        "profile_url",
        "town",
        "notes",
        "source",
    }
    mapping = validator.validated_data.get("mapping") or {key: key for key in fields}
    if set(mapping) - fields:
        raise serializers.ValidationError({"mapping": "Map only supported contact fields."})
    rows, valid, seen = [], [], set()
    try:
        for index, row in enumerate(reader, 2):
            if len(rows) >= 500:
                raise serializers.ValidationError("Import at most 500 rows at a time.")
            payload = {
                key: (row.get(column) or "").strip()
                for key, column in mapping.items()
                if column in row
            }
            serializer = ContactSerializer(data=payload)
            if not serializer.is_valid():
                email = payload.get("email", "").strip().lower()
                if email and Contact.objects.filter(email__iexact=email).exists():
                    rows.append({"row": index, "status": "duplicate", "email": email})
                    continue
                rows.append({"row": index, "status": "invalid", "errors": serializer.errors})
                continue
            item = dict(serializer.validated_data)
            email = item.get("email", "")
            if email and (email in seen or Contact.objects.filter(email__iexact=email).exists()):
                status = "duplicate"
            elif email and Suppression.objects.filter(email__iexact=email).exists():
                status = "suppressed"
            else:
                status = "ready"
                valid.append(item)
            if email:
                seen.add(email)
            rows.append({"row": index, "status": status, "name": item["name"], "email": email})
    except (csv.Error, UnicodeError) as error:
        raise serializers.ValidationError("The CSV could not be read.") from error
    if not rows:
        raise serializers.ValidationError("The CSV has no contact rows.")
    return {
        "rows": rows,
        "ready": len(valid),
        "columns": reader.fieldnames,
        "preview_token": signing.dumps(valid, salt=SALT, compress=True),
    }
