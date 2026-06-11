from rest_framework.routers import SimpleRouter
from .views import (
    CustomerViewset,
    GroupsViewset,
    ServiceViewset,
    RecordViewset,
    PaymentViewset,
)

router = SimpleRouter()

# registers
router.register("groups", GroupsViewset, basename="groups")
router.register("customers", CustomerViewset, basename="customers")
router.register("services", ServiceViewset, basename="services")
router.register("records", RecordViewset, basename="records")
router.register("payments", PaymentViewset, basename="payments")

urlpatterns = router.urls
