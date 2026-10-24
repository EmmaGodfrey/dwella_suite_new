from django.urls import path

from .email_verification import EmailVerificationConfirmView, EmailVerificationView
from .invitations import InvitationAcceptView, InvitationPreviewView
from .registration import RegistrationView
from .tours import GuidedTourView
from .views import (
    CurrentUserAvatarView,
    CurrentUserView,
    HandyAgentConfigView,
    HandyAgentTokenView,
    IdentityVerificationSubmitView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    TwoFactorDisableView,
    TwoFactorLoginVerifyView,
    TwoFactorSetupVerifyView,
    TwoFactorSetupView,
)

app_name = "accounts"

urlpatterns = [
    path("guided-tour/", GuidedTourView.as_view(), name="guided-tour"),
    path("invitations/preview/", InvitationPreviewView.as_view(), name="invitation-preview"),
    path("invitations/accept/", InvitationAcceptView.as_view(), name="invitation-accept"),
    path("email-verification/", EmailVerificationView.as_view(), name="email-verification"),
    path(
        "email-verification/confirm/",
        EmailVerificationConfirmView.as_view(),
        name="email-verification-confirm",
    ),
    path("handy-agent/config/", HandyAgentConfigView.as_view(), name="handy-agent-config"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegistrationView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("login/2fa/", TwoFactorLoginVerifyView.as_view(), name="login-2fa"),
    path("me/", CurrentUserView.as_view(), name="me"),
    path("me/avatar/", CurrentUserAvatarView.as_view(), name="me-avatar"),
    path("me/verification/", IdentityVerificationSubmitView.as_view(), name="me-verification"),
    path("handy-agent/token/", HandyAgentTokenView.as_view(), name="handy-agent-token"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("2fa/setup/", TwoFactorSetupView.as_view(), name="2fa-setup"),
    path("2fa/verify/", TwoFactorSetupVerifyView.as_view(), name="2fa-verify"),
    path("2fa/disable/", TwoFactorDisableView.as_view(), name="2fa-disable"),
]
