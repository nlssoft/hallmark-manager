from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DUserAdmin
from django.utils import timezone
from datetime import timedelta


from .models import (
    User,
    Profile,
    SubscriptionPlan,
    UserSubscription,
    UserSubscriptionHistory,
    RazorpayEvent,
)

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
    ]


# Action for UserSubscription


def extend_trial_30(modeladmin, request, queryset):
    for sub in queryset:
        sub.trial_end = max(sub.trial_end, timezone.now()) + timedelta(days=30)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):

    @admin.display(description="Days Left", ordering="current_period_end")
    def time_left(self, obj):
        if obj.current_period_end:
            return obj.current_period_end - timezone.now()
        else:
            return "N/A"

    list_display = [
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

    search_fields = [
        "user__username",
        "subscription_plan__tier",
    ]

    list_filter = ["status", "razorpay_status", ExpiringSoonFilter]

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


@admin.register(UserSubscriptionHistory)
class UserSubscriptionHistoryAdmin(admin.ModelAdmin):

    list_display = [
        "user_subscription",
        "razorpay_payment_id",
        "amount",
        "processed_at",
        "status",
    ]

    list_filter = []
