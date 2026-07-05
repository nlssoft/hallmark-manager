from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DUserAdmin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.db import transaction
from django.db.models import Q

from .models import (
    User,
    Profile,
    SubscriptionPlan,
    Subscription,
    SubscriptionHistory,
    RazorpayEvent,
)
from razorpay_client import client as razorpay
from .filters import ExpiringSoonFilter

# need to think about what to do???
from django.contrib.auth.models import Group
from django.contrib.admin.sites import NotRegistered


class ProfileAdmin(admin.StackedInline):
    model = Profile
    can_delete = False


@admin.register(User)
class UserAdmin(DUserAdmin):
    inlines = [ProfileAdmin]

    def phone_number(self, obj):
        return obj.profile.number

    def company_name(self, obj):
        return obj.profile.company_name

    def company_address(self, obj):
        return obj.profile.company_address

    def get_groups(self, obj):
        return ", ".join(g.name for g in obj.groups.all())

    list_display = (
        "username",
        "email",
        "phone_number",
        "company_name",
        "company_address",
        "parent",
        "is_staff",
        "is_active",
        "get_groups",
    )

    search_fields = (
        "username",
        "email",
        "phone_number",
        "company_name",
    )

    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
    )

    fieldsets = (
        (
            None,
            {
                "fields": ("username", "password"),
            },
        ),
        (
            "Personal info",
            {
                "fields": ("email", "email_verified", "parent"),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
        ("Groups", {"fields": ("groups",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "email_verified",
                    "parent",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    get_groups.short_description = "Groups"


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):

    list_display = [
        "__str__",
        "tier",
        "period",
        "price",
        "razorpay_plan_id",
        "max_employees",
        "max_services",
        "max_assignments_per_customer",
    ]


# stand Alone functions


@admin.action(description="⏱ Extend trial by 30 days")
def extend_trial_30(modeladmin, request, queryset):
    for sub in queryset:
        sub.trial_end = max(sub.trial_end, timezone.now()) + timedelta(days=30)
        sub.razorpay_status = "manual"
        sub.save(update_fields=["trial_end", "razorpay_status"])
    modeladmin.message_user(
        request, f"{queryset.count()} trial(s) extended 30 days.", messages.SUCCESS
    )


@transaction.atomic()
def force_activate(modeladmin, request, queryset, days, action):
    today = timezone.now()

    if queryset.filter(subscription_plan__isnull=True).exists():
        modeladmin.message_user(
            request,
            "One or more user has no Subscription plan.",
            level=messages.ERROR,
        )
        return

    elif queryset.filter(~Q(subscription_plan__period=action)).exists():
        modeladmin.message_user(
            request,
            "One or more user has a different selected plan period then the action.",
            level=messages.ERROR,
        )
        return

    queryset.update(
        status="active",
        razorpay_status="manual",
        razorpay_subscription_id=None,
        current_period_start=today,
        current_period_end=today + timedelta(days=days),
    )

    history = [
        SubscriptionHistory(
            subscription=us,
            amount=us.subscription_plan.price,
            status="manual",
        )
        for us in queryset
    ]

    SubscriptionHistory.objects.bulk_create(history)

    modeladmin.message_user(
        request,
        f"{queryset.count()}  activated for {days} days (no Razorpay). Payment records have been created with default price.",
        messages.SUCCESS,
    )


@admin.action(description="✅ Force activate — 30 days (manual)")
def force_activate_30(modeladmin, request, queryset):
    force_activate(modeladmin, request, queryset, 30, "monthly")


@admin.action(description="✅ Force activate — 180 days (manual)")
def force_activate_180(modeladmin, request, queryset):
    force_activate(modeladmin, request, queryset, 180, "semi-annually")


@admin.action(description="✅ Force activate — 365 days (manual)")
def force_activate_365(modeladmin, request, queryset):
    force_activate(modeladmin, request, queryset, 365, "annually")


@admin.action(description="Force Cancel")
def force_cancel(modeladmin, request, queryset):
    queryset.update(
        status="cancelled",
        razorpay_status="manual_cancelled",
    )
    modeladmin.message_user(
        request, f"{queryset.count()} subscription(s) cancelled.", messages.WARNING
    )


@admin.action(description=" Force Cancel Razorpay")
def force_cancel_razorpay(modeladmin, request, queryset):
    cancelled_count = 0
    failed = []
    skipped_count = 0

    for sub in queryset:
        # clean up any orphaned "previous" subscription from an in-flight upgrade
        if sub.previous_razorpay_subscription_id:
            try:
                razorpay.subscription.cancel(
                    sub.previous_razorpay_subscription_id, {"cancel_at_cycle_end": 0}
                )
            except Exception as e:
                failed.append(
                    f"{sub.pk} previous sub ({sub.previous_razorpay_subscription_id}): {e}"
                )
            sub.previous_razorpay_subscription_id = None

        if not sub.razorpay_subscription_id:
            # no razorpay subscription linked (cash-based) — just mark cancelled
            sub.status = "cancelled"
            sub.razorpay_status = "manual_cancelled"
            sub.save(
                update_fields=[
                    "status",
                    "razorpay_status",
                    "previous_razorpay_subscription_id",
                ]
            )
            skipped_count += 1
            continue

        try:
            razorpay.subscription.cancel(
                sub.razorpay_subscription_id, {"cancel_at_cycle_end": 0}
            )
        except Exception as e:
            failed.append(f"{sub.pk} ({sub.razorpay_subscription_id}): {e}")
            sub.save(
                update_fields=["previous_razorpay_subscription_id"]
            )  # still persist the cleared "previous" id
            continue

        sub.status = "cancelled"
        sub.razorpay_status = "manual_cancelled"
        sub.save(
            update_fields=[
                "status",
                "razorpay_status",
                "previous_razorpay_subscription_id",
            ]
        )
        cancelled_count += 1

    if cancelled_count:
        modeladmin.message_user(
            request,
            f"{cancelled_count} subscription(s) cancelled on Razorpay.",
            messages.WARNING,
        )
    if skipped_count:
        modeladmin.message_user(
            request,
            f"{skipped_count} subscription(s) had no Razorpay id — marked cancelled directly.",
            messages.INFO,
        )
    if failed:
        modeladmin.message_user(
            request,
            f"Failed to cancel {len(failed)} on Razorpay: {'; '.join(failed)}",
            messages.ERROR,
        )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):

    actions = [
        extend_trial_30,
        force_activate_30,
        force_activate_180,
        force_activate_365,
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return Subscription.objects.filter(
            user__parent=None, user__is_superuser=False
        ).select_related("user", "subscription_plan")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(
                parent=None,
                is_superuser=False,
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description="Time Left", ordering="current_period_end")
    def time_left(self, obj):
        if obj.current_period_end:
            left = obj.current_period_end - timezone.now()
        else:
            left = obj.trial_end - timezone.now()

        return max(left, timedelta(0))

    list_display = [
        "__str__",
        "user",
        "subscription_plan",
        "created_at",
        "status",
        "razorpay_subscription_id",
        "razorpay_status",
        "trial_end",
        "current_period_start",
        "current_period_end",
        "time_left",
    ]

    search_fields = ["user__username"]

    list_filter = [
        "subscription_plan__tier",
        "status",
        "razorpay_status",
        ExpiringSoonFilter,
    ]

    ordering = ["-current_period_end"]


@admin.register(RazorpayEvent)
class RazorpayEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "event_type", "processed_at")
    list_filter = ("event_type",)
    search_fields = ("event_id",)
    readonly_fields = ("event_id", "event_type", "processed_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SubscriptionHistory)
class SubscriptionHistoryAdmin(admin.ModelAdmin):

    list_display = [
        "subscription",
        "razorpay_payment_id",
        "amount",
        "processed_at",
        "status",
    ]

    search_fields = [
        "subscription__user__username",
        "subscription__razorpay_subscription_id",
        "razorpay_payment_id",
    ]

    list_filter = ["status"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if obj == None:
            return True
        return obj.status == "manual"
