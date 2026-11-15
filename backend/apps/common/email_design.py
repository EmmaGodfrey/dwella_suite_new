"""One branded layout for every Dwella email.

Callers keep writing the plain-text body they always sent; ``branded_email``
adds a matching HTML version (logo, heading, action button, code block) so
mail clients that render HTML show a designed message and the rest still get
readable text.
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import urlize
from django.utils.safestring import mark_safe

TEMPLATE = "email/dwella.html"


def _paragraph(text):
    # urlize escapes the text first; only the links and line breaks are markup.
    return mark_safe(urlize(text, nofollow=True, autoescape=True).replace("\n", "<br>"))


def text_paragraphs(text, *, drop=()):
    """Split a plain-text body into paragraphs, leaving out any that mention
    ``drop`` values (an action link shown as a button, for example)."""
    drop = [value for value in drop if value]
    return [
        part.strip()
        for part in str(text).split("\n\n")
        if part.strip() and not any(value in part for value in drop)
    ]


def render_email_html(
    *,
    heading,
    paragraphs,
    eyebrow="",
    action_url="",
    action_label="Open Dwella",
    code="",
    note="",
    footer="",
    preheader="",
):
    return render_to_string(
        TEMPLATE,
        {
            "heading": heading,
            "eyebrow": eyebrow,
            "paragraphs": [_paragraph(item) for item in paragraphs],
            "action_url": action_url,
            "action_label": action_label,
            "code": code,
            "note": note,
            "footer": footer,
            "preheader": preheader or (paragraphs[0] if paragraphs else ""),
            "site_url": settings.MARKETING_SITE_URL.rstrip("/"),
        },
    )


def branded_email(
    subject,
    body,
    to,
    *,
    heading=None,
    paragraphs=None,
    eyebrow="",
    action_url="",
    action_label="Open Dwella",
    code="",
    note="",
    footer="",
    from_email=None,
    **kwargs,
):
    """Return an email with ``body`` as text and the branded layout as HTML.

    Paragraphs default to the text body, minus the one carrying ``action_url``
    because the button and its fallback link already show it.
    """
    message = EmailMultiAlternatives(
        subject, body, from_email or settings.DEFAULT_FROM_EMAIL, to, **kwargs
    )
    if paragraphs is None:
        paragraphs = text_paragraphs(body, drop=[action_url])
    message.attach_alternative(
        render_email_html(
            heading=heading or subject,
            paragraphs=paragraphs,
            eyebrow=eyebrow,
            action_url=action_url,
            action_label=action_label,
            code=code,
            note=note,
            footer=footer,
        ),
        "text/html",
    )
    return message
