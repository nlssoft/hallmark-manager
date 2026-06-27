from rest_framework.routers import SimpleRouter
from django.urls import path

from .views import (
    CustomerViewset,
    GroupsViewset,
    ServiceViewset,
    RecordViewset,
    PaymentViewset,
    AuditLogViewset,
    RequestViewset,
    RecordSummaryView,
)

router = SimpleRouter()

# registers
router.register("groups", GroupsViewset, basename="groups")
router.register("customers", CustomerViewset, basename="customers")
router.register("services", ServiceViewset, basename="services")
router.register("records", RecordViewset, basename="records")
router.register("payments", PaymentViewset, basename="payments")
router.register("audit-log", AuditLogViewset, basename="audit-log")
router.register("requests", RequestViewset, basename="requests")


urlpatterns = [
    path("summary/records/", RecordSummaryView.as_view()),
] + router.urls
