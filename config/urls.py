"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from dj_rest_auth.views import PasswordResetConfirmView
from user.views import (
    CustomRegisterView,
    VerifyEmailOTPView,
    ResendVerifyEmailOTPView,
    CustomCookieTokenRefreshView,
    CustomUserDetailView,
    ChangeEmailOTPView,
    ResendChangeEmailOTPView,
)
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/token/refresh/", CustomCookieTokenRefreshView.as_view()),
    path("auth/verify-email/", VerifyEmailOTPView.as_view()),
    path("auth/resend-verify-email-otp/", ResendVerifyEmailOTPView.as_view()),
    path("auth/change-email/", ChangeEmailOTPView.as_view()),
    path("auth/resend-change-email/", ResendChangeEmailOTPView.as_view()),
    path("auth/accounts/", include("allauth.urls")),
    path("auth/user/", CustomUserDetailView.as_view(), name="rest_user_details"),
    path(
        "auth/password/reset/confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", CustomRegisterView.as_view()),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
