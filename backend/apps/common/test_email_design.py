"""Every Dwella email carries the branded HTML layout next to its text body."""

from django.core import mail

from apps.common.email_design import branded_email, text_paragraphs


def html_of(message):
    return dict((kind, body) for body, kind in message.alternatives)["text/html"]


def test_text_body_is_kept_and_html_shows_button_once():
    url = "https://app.example.com/accept?token=abc"
    message = branded_email(
        "Your invitation", f"You are invited.\n\n{url}\n\nExpires soon.", ["a@example.com"],
        action_url=url, action_label="Accept invitation",
    )
    assert message.body == f"You are invited.\n\n{url}\n\nExpires soon."
    html = html_of(message)
    assert "Accept invitation" in html
    assert "You are invited." in html and "Expires soon." in html
    # Shown as the button and the copy-paste fallback, not as a bare paragraph too.
    assert html.count(f'href="{url}"') == 2


def test_user_text_is_escaped_but_links_work():
    message = branded_email(
        "Notice", "Hello <script>alert(1)</script>\n\nSee https://dwella.properties/help",
        ["a@example.com"],
    )
    html = html_of(message)
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert 'href="https://dwella.properties/help"' in html


def test_code_is_shown_large_and_paragraphs_can_be_replaced():
    message = branded_email(
        "Code", "Your code is 123456.", ["a@example.com"],
        paragraphs=["Enter this code."], code="123456",
    )
    html = html_of(message)
    assert "Enter this code." in html and "123456" in html
    assert "Your code is" not in html


def test_text_paragraphs_drop_the_action_link():
    assert text_paragraphs("One\n\nOpen: https://x.test/a\n\nTwo", drop=["https://x.test/a"]) == [
        "One", "Two",
    ]


def test_branded_email_sends_through_the_configured_backend(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    assert branded_email("Hi", "Body", ["a@example.com"]).send() == 1
    assert mail.outbox[0].alternatives[0][1] == "text/html"
