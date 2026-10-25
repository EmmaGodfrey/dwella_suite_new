import logging

from django.conf import settings
from django.core.mail import send_mail

from apps.common.mail import delivery_configured

logger = logging.getLogger(__name__)


def send_account_mail(subject, body, recipient):
    # Never put recovery/invitation/verification secrets in console output.
    if not delivery_configured():
        return False
    try:
        return (
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
            == 1
        )
    except Exception:
        logger.warning("Account mail delivery failed")
        return False
