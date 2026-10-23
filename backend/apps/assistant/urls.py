from django.urls import path

from .views import (
    CreateDraftLeaseView,
    CreateInvoiceView,
    CreateMaintenanceCommentView,
    CreateMaintenanceRequestView,
    CreatePropertyView,
    CreateTenantView,
    CreateUnitView,
    CreateVendorView,
    RecordInvoicePaymentView,
)

app_name = "assistant"

urlpatterns = [
    path("properties/", CreatePropertyView.as_view(), name="create-property"),
    path("units/", CreateUnitView.as_view(), name="create-unit"),
    path("tenants/", CreateTenantView.as_view(), name="create-tenant"),
    path("draft-leases/", CreateDraftLeaseView.as_view(), name="create-draft-lease"),
    path("invoices/", CreateInvoiceView.as_view(), name="create-invoice"),
    path(
        "invoices/<uuid:public_id>/payments/",
        RecordInvoicePaymentView.as_view(),
        name="record-invoice-payment",
    ),
    path("vendors/", CreateVendorView.as_view(), name="create-vendor"),
    path(
        "maintenance-requests/",
        CreateMaintenanceRequestView.as_view(),
        name="create-maintenance-request",
    ),
    path(
        "maintenance-requests/<uuid:public_id>/comments/",
        CreateMaintenanceCommentView.as_view(),
        name="create-maintenance-comment",
    ),
]
