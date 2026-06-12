from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError


def get_reason(request):
    reason = request.query_params.get("reason", "").strip() or None
    requires = request.user.profile.setting_reason

    if requires and reason is None:
        raise ValidationError({"message": "Reason is required."})

    return reason, None
