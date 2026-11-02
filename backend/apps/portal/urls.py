from django.urls import path

from apps.billing import deposit_views, proof_views

from . import views

urlpatterns = [
    path("deposits/", deposit_views.TenantDepositsView.as_view()),
    path("deposit-evidence/<uuid:public_id>/", deposit_views.TenantEvidenceFileView.as_view()),
    path(
        "deposit-deductions/<uuid:public_id>/respond/",
        deposit_views.TenantDeductionResponseView.as_view(),
    ),
    path("payment-proofs/", proof_views.TenantProofListView.as_view()),
    path(
        "payment-proofs/<uuid:public_id>/<str:operation>/",
        proof_views.TenantProofActionView.as_view(),
    ),
    path("payment-proof-files/<uuid:public_id>/", proof_views.TenantProofFileView.as_view()),
    path("overview/", views.OverviewView.as_view()),
    path("profile/", views.ProfileView.as_view()),
    path("leases/", views.LeaseListView.as_view()),
    path("leases/<uuid:public_id>/", views.LeaseDetailView.as_view()),
    path("leases/<uuid:public_id>/documents/", views.LeaseDocumentsView.as_view()),
    path("documents/<uuid:public_id>/<str:operation>/", views.DocumentFileView.as_view()),
    path("originals/<uuid:public_id>/pdf/", views.OriginalFileView.as_view()),
    path("invoices/", views.InvoiceListView.as_view()),
    path("invoices/<uuid:public_id>/", views.InvoiceDetailView.as_view()),
    path("invoices/<uuid:public_id>/<str:operation>/", views.InvoiceFileView.as_view()),
    path("payments/", views.PaymentListView.as_view()),
    path("payments/<uuid:public_id>/", views.ReceiptView.as_view()),
    path("maintenance/", views.MaintenanceListView.as_view()),
    path("maintenance/<uuid:public_id>/", views.MaintenanceDetailView.as_view()),
    path("maintenance/<uuid:public_id>/<str:operation>/", views.MaintenanceActionView.as_view()),
]
