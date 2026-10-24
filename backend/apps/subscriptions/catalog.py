"""Capabilities independent of roles, product tiers and billing vendors."""

from django.db import models


class Feature(models.TextChoices):
    BULK_IMPORTS = "bulk_imports", "Bulk imports"
    TENANT_PORTAL = "tenant_portal", "Tenant portal"
    ONLINE_PAYMENTS = "online_payments", "Online payments"
    LEASE_DOCUMENTS = "lease_documents", "Lease document generation"
    LEASE_SIGNING = "lease_signing", "Issue new lease signing requests"
    EMAIL_MESSAGES = "email_messages", "Manager email messages"
    SMS_MESSAGES = "sms_messages", "SMS messages"
    WHATSAPP_MESSAGES = "whatsapp_messages", "WhatsApp messages"


class Resource(models.TextChoices):
    PROPERTIES = "properties", "Stored properties"
    UNITS = "units", "Stored units"
    TENANTS = "tenants", "Stored tenant records"


# No tiers/prices have been selected. Beta access remains open unless explicitly configured.
BETA_DEFAULTS = {feature.value: True for feature in Feature}
