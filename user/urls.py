from rest_framework.routers import SimpleRouter
from .views import EmployeeView

router = SimpleRouter()


# registers
router.register("employee", EmployeeView, basename="employee")


urlpatterns = router.urls
