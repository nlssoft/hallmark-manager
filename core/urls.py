from rest_framework.routers import SimpleRouter
from .views import (CustomerViewset, GroupsViewset, ServiceViewset, RecordViewset)

router = SimpleRouter()

# registers
router.register("groups", GroupsViewset, basename="groups")
router.register("customers", CustomerViewset, basename="customers")
router.register("services", ServiceViewset, basename="services")
router.register("records", RecordViewset, basename='records')

urlpatterns = router.urls