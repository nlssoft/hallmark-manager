from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from .models import (
    Groups,
    Customer,
    Service,
    GroupRate,
    Record,
    Payment,
    AuditLog,
)

from .custome_views import ReadOnlyModelAdmin

from django.db.models import (
    Sum,
    DecimalField,
    Value,
    Q,
    OuterRef,
    ExpressionWrapper,
    F,
    Subquery,
    Case,
    When,
)
from django.db.models.functions import Coalesce


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    @admin.display(description="Due", ordering="_due")
    def get_due(self, obj):
        return obj._due

    @admin.display(description="Surplus", ordering="_surplus")
    def get_surplus(self, obj):
        return obj._surplus

    @admin.display(description="Customers")
    def get_assigned_to(self, obj):
        employee = obj.assigned_to.all()
        if not employee:
            return "—"
        rows = format_html_join(
            mark_safe(""), "<li>{}</li>", ((e.username,) for e in employee)
        )
        return format_html('<ul style="margin:0; padding-left:1.1em;">{}</ul>', rows)

    list_display = [
        "owner",
        "logo",
        "name",
        "number",
        "email",
        "address",
        "get_assigned_to",
        "group",
        "get_due",
        "get_surplus",
    ]
    search_fields = [
        "owner__username",
        "logo",
        "name",
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        user = request.user

        if user.is_superuser:
            base = Customer.objects.with_totals().all()
        else:
            base = Customer.objects.with_totals().filter(
                Q(owner=user) | Q(assigned_to=user)
            )

        return (
            base.select_related(
                "group",
                "owner",
            )
            .prefetch_related("assigned_to")
            .order_by("-pk")
        )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        "owner",
        "name",
    ]
    search_fields = [
        "owner__username",
        "name",
    ]


@admin.register(GroupRate)
class GroupRateAdmin(admin.ModelAdmin):

    @admin.display(description="Customers")
    def get_customers(self, obj):
        names = list(obj.group.customer_set.values_list("name", flat=True))
        if not names:
            return "—"
        if len(names) > 3:
            return f"{', '.join(names[:3])} +{len(names)-3} more"
        return ", ".join(names)

    @admin.display(description="owner")
    def get_owner(self, obj):
        return obj.group.owner

    list_display = [
        "get_owner",
        "group__name",
        "group__description",
        "service",
        "rate",
        "get_customers",
    ]

    search_fields = ["group__name"]

    list_filter = [
        "service",
        "rate",
    ]

    def get_queryset(self, request):
        return GroupRate.objects.prefetch_related("group__customer_set")


@admin.register(AuditLog)
class AuditLogAdmin(ReadOnlyModelAdmin):
    list_display = [
        "user",
        "logged_at",
        "before",
        "after",
        "model",
        "action",
        "reason",
    ]
    search_fields = [
        "user__username",
    ]
    list_filter = [
        "logged_at",
        "model",
        "action",
    ]
