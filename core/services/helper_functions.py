from rest_framework.exceptions import ValidationError
from django.utils.dateparse import parse_date
from user.models import Employee, Profile
from django.db.models import Q

# def get_reason(request):
#     reason = request.query_params.get("reason", "").strip() or None
#     requires = request.user.profile.setting_reason

#     if requires and reason is None:
#         raise ValidationError("Reason is required.")

#     return reason


# for Audit log
def get_reason(request):

    reason = request.query_params.get("reason", "").strip() or None

    profile = getattr(request.user, "profile", None)
    requires = bool(profile and profile.setting_reason)

    if requires and reason is None:
        raise ValidationError("Reason is required.")

    return reason


# for summary endpoint


def get_customer_ids(request):

    raw = request.query_params.get("customer_ids")

    if not raw:
        return None

    return [
        int(customer_id)
        for customer_id in raw.split(",")
        if customer_id.strip().isdigit()
    ]


def get_employee_id(request):

    raw = request.query_params.get("employee_ids")

    if not raw:
        return None

    ids = [int(id) for id in raw.split(",") if id.strip().isdigit()]

    employee = Employee.objects.filter(pk__in=ids, parent=request.user)

    if employee.count() != len(ids):
        raise ValidationError("One  or more Employee not found.")

    return ids


def get_date_range(request):

    date_from = parse_date(request.query_params.get("from", ""))
    date_to = parse_date(request.query_params.get("to", ""))

    return date_from, date_to


def get_include_header(request):

    include_header = request.query_params.get("include_header", "false") == "true"

    if include_header:
        return (
            Profile.objects.filter(Q(owner=request.user) | Q(owner=request.user.parent))
            .values(
                "company_name",
                "company_address",
                "office_number1",
                "office_number2",
            )
            .first()
        )
