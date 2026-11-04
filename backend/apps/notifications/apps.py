from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    verbose_name = "Notifications"

    def ready(self):
        from . import events  # noqa: F401
        from .whatsapp.conversation import register_money_adapter
        from .whatsapp.proof_flow import ADAPTER

        register_money_adapter(ADAPTER)
