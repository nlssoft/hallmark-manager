from django.db.models import Count, Q
from rest_framework.exceptions import ValidationError

from ..models import Employee, TemporaryPendingPlanChange
from core.models import Customer, Service, CustomerAssignment


class SubscriptionHelperFN:

    @staticmethod
    def need_reducing(user, new_plan):
        customer = list(
            Customer.objects.filter(owner=user)
            .annotate(employee_count=Count("assigned_to"))
            .filter(employee_count__gt=new_plan.max_assignments_per_customer)
            .prefetch_related("assigned_to")
        )

        service = (
            list(user.service.all())
            if (
                new_plan.max_services is not None
                and user.service.all().count() > new_plan.max_services
            )
            else None
        )

        employee = (
            list(user.employee.all())
            if (
                new_plan.max_employees is not None
                and user.employee.count() > new_plan.max_employees
            )
            else None
        )

        return customer, employee, service

    @staticmethod
    def create_temporary_plan_changes(customer, employee, service, request, new_plan):
        customer_assignments = None
        employee_id = None
        service_id = None

        if customer:
            c_e_id = request.data.get(
                "customer_employee_id"
            )  #  this value should be a dict

            customer_assignments = {}
            customer_map = {c.pk: c for c in customer}

            if not isinstance(c_e_id, dict):
                raise ValidationError(
                    {"error": "customer_employee_id must be a dictionary."},
                )

            for customer_id, employee_id in c_e_id.items():
                c = customer_map.get(customer_id)
                if c is None:
                    raise ValidationError(
                        {"error": "Data does not match"},
                    )

                # making suer employee id is always a list
                if not isinstance(employee_id, list):
                    employee_id = [employee_id]  # removing duplicate if any

                employee_id = set(employee_id)

                assigned_to_ids = {e.id for e in c.assigned_to.all()}

                if not employee_id.issubset(assigned_to_ids):
                    raise ValidationError(
                        {
                            "error": "You have more active customer assignment than the selected plan allows. Disable some customer assignment before switching to this plan."
                        },
                    )

                c.employee_count -= len(employee_id)

                if c.employee_count > new_plan.max_assignments_per_customer:
                    raise ValidationError(
                        {
                            "error": "You have more active customer assignment than the selected plan allows. Disable some customer assignment before switching to this plan."
                        },
                    )
                customer_assignments[customer_id] = list(employee_id)

        if employee:
            employee_id = request.data.get("employee_id")

            if employee_id is None:
                raise ValidationError(
                    {
                        "error": "You have more active employees than the selected plan allows. Disable some employees before switching to this plan."
                    },
                )

            if not isinstance(employee_id, list):
                employee_id = [employee_id]

            employee_id = set(employee_id)

            all_employee_id = {e.id for e in employee}

            if not employee_id.issubset(all_employee_id):
                raise ValidationError(
                    {
                        "error": "You have more active employees than the selected plan allows. Disable some employees before switching to this plan."
                    },
                )

            if (
                new_plan.max_employees is not None
                and (len(employee) - len(employee_id)) > new_plan.max_employees
            ):
                raise ValidationError(
                    {
                        "error": "You have more active employees than the selected plan allows. Disable some employees before switching to this plan."
                    },
                )

        if service:
            service_id = request.data.get("service_id")

            if service_id is None:
                raise ValidationError(
                    {
                        "error": "You have more active services than the selected plan allows. Disable some services before switching to this plan."
                    },
                )

            if not isinstance(service_id, list):
                service_id = [service_id]

            service_id = set(service_id)

            all_service_id = {s.id for s in service}

            if not service_id.issubset(all_service_id):
                raise ValidationError(
                    {
                        "error": "You have more active services than the selected plan allows. Disable some services before switching to this plan."
                    },
                )

            if (
                new_plan.max_services is not None
                and (len(service) - len(service_id)) > new_plan.max_services
            ):
                raise ValidationError(
                    {
                        "error": "You have more active services than the selected plan allows. Disable some services before switching to this plan."
                    },
                )

        if any((customer, employee, service)):
            TemporaryPendingPlanChange.objects.update_or_create(
                user=request.user,
                defaults={
                    "new_plan": new_plan,
                    "employee_id": employee_id,
                    "service_id": service_id,
                    "customer_employee_id": customer_assignments,
                },
            )

    @staticmethod
    def reduce(obj):

        if obj.employee_id is not None:
            Employee.objects.filter(pk__in=obj.employee_id).update(is_active=False)
        if obj.service_id:
            Service.objects.filter(pk__in=obj.service_id).update(disabled=True)
        if obj.customer_employee_id:
            query = Q()

            for customer_id, employee_ids in obj.customer_employee_id.items():
                query |= Q(customer_id=customer_id, employee_id__in=employee_ids)

            CustomerAssignment.objects.filter(query).update(is_active=False)

    @staticmethod
    def return_benefits(user):
        user.employee.filter(is_active=False).update(is_active=True)
        user.service.filter(disable=True).update(disabled=False)

        CustomerAssignment.objects.filter(
            customer__owner=user, employee__parent=user, is_active=False
        ).update(is_active=True)
