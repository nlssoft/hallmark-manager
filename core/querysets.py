from django.db.models import (
    QuerySet,
    Sum,
    F,
    Value,
    DecimalField,
    ExpressionWrapper,
    OuterRef,
    Subquery,
    Case,
    When,
)
from django.db.models.functions import Coalesce
from django.apps import apps


class RecordQuerySet(QuerySet):

    def with_financials(self):
        Allocation = apps.get_model("core", "Allocation")
        AdvanceUsage = apps.get_model("core", "AdvanceUsage")

        allocation_total = (
            Allocation.objects.filter(record=OuterRef("pk"))
            .values("record_id")
            .annotate(
                total=Coalesce(
                    Sum("amount"),
                    Value(0),
                    output_field=DecimalField(),
                )
            )
            .values("total")
        )

        advanceusage_total = (
            AdvanceUsage.objects.filter(record=OuterRef("pk"))
            .values("record_id")
            .annotate(
                total=Coalesce(
                    Sum("amount"),
                    Value(0),
                    output_field=DecimalField(),
                )
            )
            .values("total")
        )

        return (
            self.annotate(
                _allocation_total=Coalesce(
                    Subquery(allocation_total, output_field=DecimalField()),
                    Value(0),
                    output_field=DecimalField(),
                ),
                _advanceusage_total=Coalesce(
                    Subquery(advanceusage_total, output_field=DecimalField()),
                    Value(0),
                    output_field=DecimalField(),
                ),
            )
            .annotate(
                _paid=ExpressionWrapper(
                    F("_allocation_total") + F("_advanceusage_total"),
                    output_field=DecimalField(),
                )
            )
            .annotate(
                _amount=ExpressionWrapper(
                    F("rate") * F("pcs"), output_field=DecimalField()
                )
            )
            .annotate(
                _due=F("_amount")
                - F("_paid")
                - Coalesce(F("discount"), Value(0), output_field=DecimalField())
            )
        )


class PaymentQuerySet(QuerySet):
    def with_balance(self):
        Allocation = apps.get_model("core", "Allocation")
        Advance = apps.get_model("core", "Advance")
        AdvanceUsage = apps.get_model("core", "AdvanceUsage")

        allocation_total = (
            Allocation.objects.filter(payment_id=OuterRef("pk"))
            .values("payment_id")
            .annotate(
                total=Coalesce(
                    Sum("amount"),
                    Value(0),
                    output_field=DecimalField(),
                )
            )
            .values("total")
        )

        advance_total = (
            Advance.objects.filter(payment_id=OuterRef("pk"))
            .values("payment_id")
            .annotate(
                total=Coalesce(
                    Sum("total_amount"),
                    Value(0),
                    output_field=DecimalField(),
                )
            )
            .values("total")
        )

        advanceusage_total = (
            AdvanceUsage.objects.filter(advance__payment_id=OuterRef("pk"))
            .values("advance__payment_id")
            .annotate(
                total=Coalesce(
                    Sum("amount"),
                    Value(0),
                    output_field=DecimalField(),
                )
            )
            .values("total")
        )

        return (
            self.annotate(
                _allocation_total=Coalesce(
                    Subquery(allocation_total, output_field=DecimalField()),
                    Value(0),
                    output_field=DecimalField(),
                ),
                _advance_total=Coalesce(
                    Subquery(advance_total, output_field=DecimalField()),
                    Value(0),
                    output_field=DecimalField(),
                ),
                _advanceusage_total=Coalesce(
                    Subquery(advanceusage_total, output_field=DecimalField()),
                    Value(0),
                    output_field=DecimalField(),
                ),
            )
            .annotate(
                _allocated_amount=ExpressionWrapper(
                    F("_allocation_total") + F("_advance_total"),
                    output_field=DecimalField(),
                )
            )
            .annotate(
                _unalocated_amount=ExpressionWrapper(
                    F("amount") - F("_allocated_amount"),
                    output_field=DecimalField(),
                )
            )
            .annotate(
                _used=ExpressionWrapper(
                    F("_advanceusage_total") + F("_allocation_total"),
                    output_field=DecimalField(),
                )
            )
            .annotate(
                _left=ExpressionWrapper(
                    F("amount") - F("_used"), output_field=DecimalField()
                )
            )
        )


class AdvanceQuerySet(QuerySet):
    def with_availability(self):
        return self.annotate(
            _used_already=Coalesce(
                Sum("advanceusage__amount"), Value(0), output_field=DecimalField()
            )
        ).annotate(_available=F("total_amount") - F("_used_already"))
