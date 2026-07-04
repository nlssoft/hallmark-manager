from django.db.models import Count


from ..models import Employee
from core.models import Customer, Service


class SubscriptionHelperFN:

    @staticmethod
    def perfrom_check(user, new_plan):
        queryset = list(
            Customer.objects.filter(owner=user)
            .annotate(employee_count=Count("assigned_to"))
            .filter(employee_count__gt=new_plan.max_assignments_per_customer)
            .prefetch_related("assigned_to")
        )

        employee_count = (
            new_plan.max_employees is not None
            and user.employee.all().count() > new_plan.max_employees
        )

        service_count = (
            new_plan.max_services is not None
            and user.service.all().count() > new_plan.max_services
        )
        return queryset, employee_count, service_count

    @staticmethod
    def reduce(
        disable_employee,
        disable_service,
        customer_assignement,
        new_plan,
        reduce_needed,
        user,
    ):
        employee, service, assignments = reduce_needed

        if employee:
            Employee.objects.filter(parent=user).filter(pk__in=disable_employee).update(
                active=False
            )
        if service:
            Service.objects.filter(owner=user).filter(pk__in=disable_service).update(
                disable=True
            )
        if assignments:
            customers = {
                c.pk: c
                for c in Customer.objects.filter(
                    owner=user, pk__in=customer_assignement.keys()
                )
            }
            for customer_id, employee_ids in customer_assignement.items():
                customer = customers.get(int(customer_id))

                if customer:
                    customer.assigned_to.remove(*employee_ids)

        reduce_needed = SubscriptionHelperFN.perfrom_check(user, new_plan)
        if any(reduce_needed):
            raise ValueError("Reduction incomplete, some limits still exceeded.")


class SubscriptionLimitService:

    @staticmethod
    def can_create_employee(user):
        tier = user.subscription.tier
