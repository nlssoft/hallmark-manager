from rest_framework.exceptions import ValidationError
from django.utils.dateparse import parse_date
from user.models import Employee, Profile
from django.db.models import Q
import uuid

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

    customer_ids = []

    for customer_id in raw.split(","):
        customer_id = customer_id.strip()

        try:
            customer_ids.append(uuid.UUID(customer_id))
        except ValueError:
            continue

    return customer_ids


import uuid


def get_employee_id(request):
    raw = request.query_params.get("employee_ids")

    if not raw:
        return None

    ids = []

    for employee_id in raw.split(","):
        employee_id = employee_id.strip()

        try:
            ids.append(uuid.UUID(employee_id))
        except ValueError:
            raise ValidationError(f"{employee_id} is not a valid employee ID.")

    ids = list(dict.fromkeys(ids))

    employees = Employee.objects.filter(
        public_id__in=ids,
        parent=request.user,
    )

    if employees.count() != len(ids):
        raise ValidationError("One or more employees were not found.")

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
