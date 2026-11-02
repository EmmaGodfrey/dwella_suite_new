from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import deposit_views as deposit
from . import proof_views as proof
from .views import InvoiceViewSet, PaymentInstructionViewSet, PaymentViewSet

app_name = "billing"

router = DefaultRouter()
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("payments", PaymentViewSet, basename="payment")
router.register("payment-instructions", PaymentInstructionViewSet, basename="payment-instruction")

urlpatterns = [
    path("deposits/<uuid:public_id>/", deposit.DepositView.as_view()),
    path("deposits/<uuid:public_id>/request/", deposit.DepositRequestView.as_view()),
    path("deposits/<uuid:public_id>/opening/", deposit.DepositOpeningView.as_view()),
    path("deposits/<uuid:public_id>/deductions/", deposit.DepositDeductionCreateView.as_view()),
    path("deposits/<uuid:public_id>/refunds/", deposit.DepositRefundView.as_view()),
    path("deposit-deductions/<uuid:public_id>/evidence/", deposit.DeductionEvidenceView.as_view()),
    path("deposit-evidence/<uuid:public_id>/", deposit.EvidenceFileView.as_view()),
    path(
        "deposit-deductions/<uuid:public_id>/<str:decision>/",
        deposit.DeductionDecisionView.as_view(),
    ),
    path("payment-proofs/", proof.ManagerProofListView.as_view()),
    path("payment-proofs/<uuid:public_id>/", proof.ManagerProofDetailView.as_view()),
    path(
        "payment-proofs/<uuid:public_id>/<str:decision>/",
        proof.ManagerProofDecisionView.as_view(),
    ),
    path("payment-proof-files/<uuid:public_id>/", proof.ManagerProofFileView.as_view()),
    path("", include(router.urls)),
]
