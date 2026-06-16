from rest_framework.routers import SimpleRouter
from .views import (
    CustomerViewset,
    GroupsViewset,
    ServiceViewset,
    RecordViewset,
    PaymentViewset,
    AdvanceLogViewset,
    AuditLogViewset,
    RequestViewset,
)

router = SimpleRouter()

# registers
router.register("groups", GroupsViewset, basename="groups")
router.register("customers", CustomerViewset, basename="customers")
router.register("services", ServiceViewset, basename="services")
router.register("records", RecordViewset, basename="records")
router.register("payments", PaymentViewset, basename="payments")
router.register("advance-log", AdvanceLogViewset, basename="advance-log")
router.register("audit-log", AuditLogViewset, basename="audit-log")
router.register("requests", RequestViewset, basename="requests")

urlpatterns = router.urls
