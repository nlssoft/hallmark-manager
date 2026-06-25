from django.db.models import QuerySet, Sum, F, Value, DecimalField, ExpressionWrapper,\
      OuterRef, Subquery, Case, When
from django.db.models.functions import Coalesce


class RecordQuerySet(QuerySet):
    def with_financials(self):
        return (
            self
            .annotate(
                _paid=Coalesce(Sum("allocation__amount"), Value(0), output_field=DecimalField())
                + Coalesce(Sum("advanceusage__amount"), Value(0), output_field=DecimalField()),
                _amount=ExpressionWrapper(
                    F("rate") * F("pcs"), output_field=DecimalField()
                ),
            )
            .annotate(
                _due=F("_amount") - F("_paid")
                - Coalesce(F("discount"), Value(0), output_field=DecimalField())
            )
        )


class PaymentQuerySet(QuerySet):
    def with_balance(self):
        return (
            self
            .annotate(
                _used=Coalesce(Sum("allocation__amount"), Value(0), output_field=DecimalField())
                + Coalesce(Sum("advance__total_amount"), Value(0), output_field=DecimalField())
            )
            .annotate(_left=F("amount") - F("_used"))
        )


class AdvanceQuerySet(QuerySet):
    def with_availability(self):
        return (
            self
            .annotate(
                _used_already=Coalesce(
                    Sum("advanceusage__amount"), Value(0), output_field=DecimalField()
                )
            )
            .annotate(_available=F("total_amount") - F("_used_already"))
        )