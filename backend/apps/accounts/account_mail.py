import logging

from apps.common.email_design import branded_email
from apps.common.mail import delivery_configured

logger = logging.getLogger(__name__)


def send_account_mail(subject, body, recipient, **design):
    """Send one account email: ``body`` as text plus the branded HTML layout.

    ``design`` takes branded_email options such as heading, action_url and
    action_label.
    """
    # Never put recovery/invitation/verification secrets in console output.
    if not delivery_configured():
        return False
    try:
        return branded_email(subject, body, [recipient], **design).send(fail_silently=False) == 1
    except Exception:
        logger.warning("Account mail delivery failed")
        return False
