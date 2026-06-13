from rest_framework.permissions import BasePermission


class ParentAccount_Only(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.parent_id is None
        )


class CustomerEndpointPermission(BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.parent_id is None
        )


class RequestEndpointPermission(BasePermission):

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        child = user.parent is not None

        if view.action in ["aprove", "reject"]:
            return not child

        if view.action in ["create", "update", "partial_update", "destroy"]:
            return child
