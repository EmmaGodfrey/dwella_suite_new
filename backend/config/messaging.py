"""Server-only provider configuration. Merely adding credentials never enables sending."""

import os

from .env import env_bool, env_list


def messaging_settings(backend):
    values = {
        "EMAIL_ROUTING_ENABLED": env_bool("APP_EMAIL_ROUTING_ENABLED", False),
        "EMAIL_PRIMARY_BACKEND": backend,
        "EMAIL_GOOGLE_LIMIT": int(os.getenv("APP_EMAIL_GOOGLE_LIMIT", "400")),
        "RESEND_API_KEY": os.getenv("RESEND_API_KEY", ""),
        "RESEND_FROM_EMAIL": os.getenv("RESEND_FROM_EMAIL", ""),
        "RESEND_DAILY_LIMIT": int(os.getenv("RESEND_DAILY_LIMIT", "100")),
        "RESEND_MONTHLY_LIMIT": int(os.getenv("RESEND_MONTHLY_LIMIT", "3000")),
        "WHATSAPP_ENABLED": env_bool("APP_WHATSAPP_ENABLED", False),
        "SMS_ENABLED": env_bool("APP_SMS_ENABLED", False),
        "AFRICASTALKING_USERNAME": os.getenv("AFRICASTALKING_USERNAME", ""),
        "AFRICASTALKING_API_KEY": os.getenv("AFRICASTALKING_API_KEY", ""),
        "AFRICASTALKING_SENDER_ID": os.getenv("AFRICASTALKING_SENDER_ID", ""),
        "AFRICASTALKING_CALLBACK_TOKEN": os.getenv("AFRICASTALKING_CALLBACK_TOKEN", ""),
        "AFRICASTALKING_SANDBOX": env_bool("AFRICASTALKING_SANDBOX", True),
        "WHATSAPP_ACCESS_TOKEN": os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
        "WHATSAPP_PHONE_NUMBER_ID": os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
        "WHATSAPP_BUSINESS_ACCOUNT_ID": os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", ""),
        "WHATSAPP_APP_SECRET": os.getenv("WHATSAPP_APP_SECRET", ""),
        "WHATSAPP_VERIFY_TOKEN": os.getenv("WHATSAPP_VERIFY_TOKEN", ""),
        "WHATSAPP_GRAPH_VERSION": os.getenv("WHATSAPP_GRAPH_VERSION", "v24.0"),
        "WHATSAPP_RENT_TEMPLATE": os.getenv("WHATSAPP_RENT_TEMPLATE", ""),
        "WHATSAPP_TEMPLATE_LANGUAGE": os.getenv("WHATSAPP_TEMPLATE_LANGUAGE", "en"),
        "OUTBOUND_PHONE_ALLOWLIST": env_list("APP_OUTBOUND_PHONE_ALLOWLIST", ""),
    }
    if values["EMAIL_ROUTING_ENABLED"]:
        values["EMAIL_BACKEND"] = "apps.common.email_router.EmailBackend"
    return values
