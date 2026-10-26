from django.urls import path

from . import views
from .platform_views import (
    PlatformCollectionDetail,
    PlatformPaymentConfiguration,
    PlatformTransactionsView,
    PlatformWithdrawalDetail,
)

urlpatterns = [
    path("platform/transactions/", PlatformTransactionsView.as_view()),
    path("platform/configuration/", PlatformPaymentConfiguration.as_view()),
    path("platform/collections/<uuid:public_id>/", PlatformCollectionDetail.as_view()),
    path("platform/withdrawals/<uuid:public_id>/", PlatformWithdrawalDetail.as_view()),
    path("tenant/options/", views.TenantPaymentOptionsView.as_view()),
    path("platform/balance/", views.PlatformBalanceView.as_view()),
    path("tenant/invoices/<uuid:public_id>/checkout/", views.TenantCheckoutView.as_view()),
    path("tenant/collections/", views.TenantCollectionList.as_view()),
    path("tenant/collections/<uuid:public_id>/", views.TenantCollectionDetail.as_view()),
    path("collections/", views.ManagerCollectionList.as_view()),
    path("destination/", views.ManagerDestinationView.as_view()),
    path("destination/check/", views.AccountCheckView.as_view()),
    path("banks/", views.BankListView.as_view()),
    path("payouts/", views.PayoutSummaryView.as_view()),
    path("withdrawals/", views.WithdrawalListView.as_view()),
    path("withdrawals/preview/", views.WithdrawalPreviewView.as_view()),
    path("withdrawals/<uuid:public_id>/cancel/", views.WithdrawalCancelView.as_view()),
    path("platform/destinations/<uuid:public_id>/", views.PlatformDestinationView.as_view()),
    path("platform/collections/", views.PlatformCollectionList.as_view()),
    path("platform/collections/<uuid:public_id>/exchanges/", views.PlatformExchangeList.as_view()),
    path("platform/exchanges/<uuid:public_id>/", views.PlatformExchangeDetail.as_view()),
    path("webhook/", views.WebhookView.as_view()),
]
