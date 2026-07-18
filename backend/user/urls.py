from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import EmployeeMixView
from .subscription_view import (
    CurrentSubscriptionView,
    SubscriptionPlanApiView,
    SubscriptionPlanPreviewApiView,
    SubscriptionCreateApiView,
    SubscritionStatusApiView,
    RazorpayWebhookApiView,
    SubscriptionCancelledApiView,
)

router = SimpleRouter()


# registers
router.register("employee", EmployeeMixView, basename="employee")


urlpatterns = [
    path("plans/", SubscriptionPlanApiView.as_view(), name="plans"),
    path("plans/preview/", SubscriptionPlanPreviewApiView.as_view(), name="preview"),
    path(
        "plans/preview/create/",
        SubscriptionCreateApiView.as_view(),
        name="subscription-create",
    ),
    path(
        "subscription/status/",
        SubscritionStatusApiView.as_view(),
        name="subscription-status",
    ),
    path(
        "subscription/cancelled/",
        SubscriptionCancelledApiView.as_view(),
        name="subscription-cancelled",
    ),
    path(
        "subscription/webhook/",
        RazorpayWebhookApiView.as_view(),
        name="subscription-webhook",
    ),
    path(
    "subscription/",
    CurrentSubscriptionView.as_view(),
    name="current-subscription",
)
] + router.urls
