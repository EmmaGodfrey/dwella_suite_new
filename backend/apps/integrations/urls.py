from django.urls import path

from .views import SmartInvoiceInitialiseView, SmartInvoiceSettingsView

app_name = "integrations"

urlpatterns = [
    path("smart-invoice/", SmartInvoiceSettingsView.as_view(), name="smart-invoice"),
    path(
        "smart-invoice/initialise/",
        SmartInvoiceInitialiseView.as_view(),
        name="smart-invoice-initialise",
    ),
]
