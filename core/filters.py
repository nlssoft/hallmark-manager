import django_filters
from .models import Record, Payment, Advance, AuditLog


class RecordFilter(django_filters.FilterSet):
    date_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )

    date_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = Record
        fields = ["date_after", "date_before"]


class PaymentFilter(django_filters.FilterSet):
    date_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )

    date_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = Payment
        fields = ["date_after", "date_before", "mode"]


class AdvanceLogFilter(django_filters.FilterSet):
    total_amount = django_filters.NumberFilter(
        field_name="total_amount", lookup_expr="gte"
    )
    date_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )

    date_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = Advance
        fields = ["date_after", "date_before", "total_amount"]


class AuditLogFilter(django_filters.FilterSet):
    date_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )

    date_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = AuditLog
        fields = ["date_after", "date_before", "action", "model"]
