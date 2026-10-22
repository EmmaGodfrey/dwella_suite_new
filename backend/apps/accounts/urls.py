from django.urls import path

from .registration import RegistrationView
from .views import (
    CurrentUserAvatarView,
    CurrentUserView,
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
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegistrationView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("login/2fa/", TwoFactorLoginVerifyView.as_view(), name="login-2fa"),
    path("me/", CurrentUserView.as_view(), name="me"),
    path("me/avatar/", CurrentUserAvatarView.as_view(), name="me-avatar"),
    path("me/verification/", IdentityVerificationSubmitView.as_view(), name="me-verification"),
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
