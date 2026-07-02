from datetime import timedelta
from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.utils import timezone
from django.db.models import Q


class ExpiringSoonFilter(admin.SimpleListFilter):

    title = "Expiration"
    parameter_name = "expiration"

    def lookups(self, request, model_admin):
        return [("7", "Ends in 7 days"), ("30", "Ends in 30 days")]

    def queryset(self, request: Any, queryset: QuerySet[Any]) -> QuerySet[Any] | None:
        today = timezone.now()

        if self.value() == "7":
            return queryset.filter(
                Q(
                    current_period_end__gte=today,
                    current_period_end__lte=today + timedelta(days=7),
                )
                | Q(
                    trial_end__gte=today,
                    trial_end__lte=today + timedelta(days=7),
                )
            )

        if self.value() == "30":
            return queryset.filter(
                Q(
                    current_period_end__gte=today,
                    current_period_end__lte=today + timedelta(days=30),
                )
                | Q(
                    trial_end__gte=today,
                    trial_end__lte=today + timedelta(days=30),
                )
            )

        return queryset
