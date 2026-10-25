from django.urls import path

from . import views

urlpatterns = [
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
