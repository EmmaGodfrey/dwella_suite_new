import re
from string import Formatter

from rest_framework.exceptions import ValidationError

FIELDS = (
    "first_name",
    "salutation",
    "organization",
    "platform",
    "handle",
    "audience_size",
    "town",
    "personal_line",
    "sender_first_name",
    "signature",
    "signature_short",
    "offer",
)


def validate_merge_fields(value):
    try:
        for _, field, spec, conversion in Formatter().parse(value):
            if field is not None and (field not in FIELDS or spec or conversion):
                raise ValueError("Unsupported merge field.")
    except ValueError as error:
        raise ValidationError("Use only the supported merge fields, without formatting.") from error
    return value


def render_text(value, context):
    validate_merge_fields(value)
    missing = sorted(
        {
            field
            for _, field, _, _ in Formatter().parse(value)
            if field and field != "personal_line" and not str(context.get(field, ""))
        }
    )
    if missing:
        raise ValidationError({"missing_fields": missing})
    rendered = value.format_map(context)
    if re.search(r"\{[^{}]+\}", rendered):
        raise ValidationError("The rendered message still contains an unfilled merge field.")
    return re.sub(r"\n{3,}", "\n\n", rendered).strip()


def render_template(template, contact, config, personal_line="", whatsapp=False):
    context = {key: str(getattr(contact, key, "") or "") for key in FIELDS}
    context.update(
        {
            key: getattr(config, key)
            for key in (
                "sender_first_name",
                "signature",
                "signature_short",
                "offer",
            )
        }
    )
    context["salutation"] = contact.salutation or contact.first_name
    context["personal_line"] = personal_line
    subject = render_text(template.subject, context)
    if "\n" in subject or "\r" in subject or len(subject) > 250:
        raise ValidationError({"subject": "Use a single subject line of at most 250 characters."})
    body = template.whatsapp_body if whatsapp else template.body
    if not body:
        raise ValidationError("Add a WhatsApp version to this template first.")
    return {"subject": subject, "body": render_text(body, context)}
