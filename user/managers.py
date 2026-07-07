from typing import Any

from django.contrib.auth.models import UserManager
from django.db import models
from django.db.models import (
    Q,
    Sum,
    ExpressionWrapper,
    DecimalField,
    Value,
    OuterRef,
    Subquery,
    F,
)
from django.db.models.functions import Coalesce

from django.apps import apps

"""
IMPORTANT... NOTE that this only works for Queryset update() NOT bulk opretions.
at update time it overrides is_active based on disabled so that ban/unban/subsciption_disable work.
"""


class UserQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        if "disabled" in kwargs:
            kwargs["is_active"] = not kwargs["disabled"]
        return super().update(**kwargs)


class CustomUserManager(UserManager.from_queryset(UserQuerySet)):
    pass


class EmployeeQueryset(models.QuerySet):

    def with_summary(self):
        Record = apps.get_model("core", "Record")
        Payment = apps.get_model("core", "Payment")

        records = Record.objects.for_employee(OuterRef("pk")).values(
            "customer__customerassignment__employee"
        )

        record_amount = (
            records.annotate(
                work_amount=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            F("rate") * F("pcs"), output_field=DecimalField()
                        )
                    ),
                    Value(0),
                    output_field=DecimalField(),
                )
            )
        ).values("work_amount")

        record_discount = (
            records.annotate(
                work_discount=Coalesce(
                    Sum(F("discount")), Value(0), output_field=DecimalField()
                )
            )
        ).values("work_discount")

        payment_total = (
            Payment.objects.for_employee(OuterRef("pk"))
            .values("customer__customerassignment__employee")
            .annotate(
                payment_amount=Coalesce(
                    Sum(F("amount")), Value(0), output_field=DecimalField()
                )
            )
        ).values("payment_amount")

        return self.annotate(
            work_amount=Coalesce(
                Subquery(record_amount, output_field=DecimalField()),
                Value(0),
                output_field=DecimalField(),
            ),
            work_discount=Coalesce(
                Subquery(record_discount, output_field=DecimalField()),
                Value(0),
                output_field=DecimalField(),
            ),
            payment_amount=Coalesce(
                Subquery(payment_total, output_field=DecimalField()),
                Value(0),
                output_field=DecimalField(),
            ),
        )


class EmployeeManager(models.Manager.from_queryset(EmployeeQueryset)):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(parent__isnull=False)
