"""Apply runtime sender metadata and a shared SMTP budget below recipient guards."""

from django.conf import settings
from django.core.mail import get_connection
from django.core.mail.backends.base import BaseEmailBackend

from apps.audit.runtime_settings import runtime_settings, sender_identity

from .email_router import EmailDeliveryUnknown, reserve_provider


class RuntimeEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.inner = get_connection(
            settings.RUNTIME_MAIL_INNER_BACKEND, fail_silently=False, **kwargs
        )
        self.managed = False

    def open(self):
        self.managed = True
        return self.inner.open()

    def close(self):
        self.managed = False
        return self.inner.close()

    def send_messages(self, messages):
        sent = 0
        try:
            for message in messages:
                if not message.recipients():
                    continue
                config = runtime_settings()
                if message.from_email == settings.DEFAULT_FROM_EMAIL:
                    message.from_email = sender_identity(config)
                if not message.reply_to and config["email_reply_to"]:
                    message.reply_to = [config["email_reply_to"]]
                # The optional router reserves its own quota. Never double reserve
                # or introduce a Resend fallback for ordinary SMTP mail.
                if settings.RUNTIME_MAIL_INNER_BACKEND != "apps.common.email_router.EmailBackend":
                    reserve_provider(len(message.recipients()), allow_fallback=False)
                if settings.RUNTIME_MAIL_INNER_BACKEND == "apps.common.email_router.EmailBackend":
                    sent += self.inner.send_messages([message]) or 0
                else:
                    try:
                        sent += self.inner.send_messages([message]) or 0
                    except Exception:
                        raise EmailDeliveryUnknown("SMTP send needs review.") from None
            return sent
        except Exception:
            if not self.fail_silently:
                raise
            return sent
        finally:
            if not self.managed:
                try:
                    self.inner.close()
                except Exception:
                    pass
