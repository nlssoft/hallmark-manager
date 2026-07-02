from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import EmployeeView
from .subscription_view import (
    SubscriptionCreateApiView, 
    SubscritionStatusApiView, 
    RazorpayWebhookApiView, 
    SubscriptionCancelledApiView
)



router = SimpleRouter()


# registers
router.register("employee", EmployeeView, basename="employee")


urlpatterns =[
    path("subscription/create/", SubscriptionCreateApiView.as_view(), name="subscription-create"),
    path("subscription/status/", SubscritionStatusApiView.as_view(), name="subscription-status"),
    path("subscription/cancelled/", SubscriptionCancelledApiView.as_view(), name="subscription-cancelled"),
    path("subscription/webhook/", RazorpayWebhookApiView.as_view(), name="subscription-webhook"),

] + router.urls
