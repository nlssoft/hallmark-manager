from rest_framework.permissions import BasePermission
from user.models import UserSubscription


class IsSubscriptionActive(BasePermission):
    message = "Your subscription is inactive. Please subscribe or renew."

    def has_permission(self, request, view):

        if view.action in ("list", "retrieve"):
            return True

        else:
            return False

    def has_object_permission(self, request, view, obj):
        try:
            return request.user.subscription.is_active
        except UserSubscription.DoesNotExist:
            return False
