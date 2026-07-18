from django.db import transaction
from django.db.models import Count
from rest_framework.exceptions import ValidationError
from core.models import CustomerAssignment, Customer


class PlanLimit:
    TRIAL_PLAN = {
        "max_employees": 4,
        "max_services": 5,
        "max_assignments_per_customer": 2,
    }

    def __init__(self, subscription):
        self.subscription = subscription

    def _get(self, field):
        if self.subscription.status == "trial":
            return self.TRIAL_PLAN[field]

        plan = self.subscription.plan
        return getattr(plan, field) if plan else 0


class PlanLimitChecker:

    def __init__(self, owner):
        self.owner = owner
        self.limits = PlanLimit(owner.subscription)

    @transaction.atomic
    def assert_can_add_employee(self):
        limit = self.limits._get("max_employees")
        if limit is None:
            return
        current = self.owner.employee.select_for_update().filter(disabled=False).count()

        if current >= limit:
            raise ValidationError(f"Employee limit reached ({limit})")

    @transaction.atomic
    def assert_can_add_service(self):
        limit = self.limits._get("max_services")
        if limit is None:
            return
        current = self.owner.service.select_for_update().filter(disabled=False).count()

        if current >= limit:
            raise ValidationError(f"Service limit reached ({limit})")

    @transaction.atomic()
    def assert_can_add_assignments(self, customer_ids, exclude_employee=None):
        limit = self.limits._get("max_assignments_per_customer")
        if limit is None or not customer_ids:
            return

        qs = CustomerAssignment.objects.filter(
            customer_id__in=customer_ids, active=True
        )

        if exclude_employee:
            qs = qs.exclude(employee=exclude_employee)

        counts = qs.values("customer_id").annotate(n=Count("id"))
        count_map = {row["customer_ids"]: row["n"] for row in counts}

        violation = {cid for cid in customer_ids if count_map(cid, 0) + 1 > limit}

        if violation:
            pk = Customer.object.filter(pk__in=violation).values_list("pk", flat=True)
            raise ValidationError(
                f"Assignment limit ({limit}) reached for: {', '.join(pk)}"
            )
