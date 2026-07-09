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
    VerifyEmailChangeOTPView,
    ResendEmailChangeOTPView,
)
from django.conf import settings

urlpatterns = [
    # refrest token url
    path("auth/token/refresh/", CustomCookieTokenRefreshView.as_view()),
    # after registration email url
    path("auth/verify-email/", VerifyEmailOTPView.as_view()),
    path("auth/resend-verify-email-otp/", ResendVerifyEmailOTPView.as_view()),
    # email change urls
    path("auth/change-email/", VerifyEmailChangeOTPView.as_view()),
    path("auth/resend-change-email/", ResendEmailChangeOTPView.as_view()),
    # custom UserDetail url
    path("auth/user/", CustomUserDetailView.as_view(), name="rest_user_details"),
    # password reset urls
    path(
        "auth/password/reset/confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # librais
    path("admin/", admin.site.urls),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", CustomRegisterView.as_view()),
    # apps
    path("user/", include("user.urls")),
    path("core/", include("core.urls")),
]

if settings.DEBUG:
    import debug_toolbar
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
    from django.views.decorators.csrf import ensure_csrf_cookie
    from django.http import JsonResponse

    @ensure_csrf_cookie
    def csrf_token_view(request):
        return JsonResponse({"detail": "ok"})

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema")),
        path("csrf/", csrf_token_view),
    ]
