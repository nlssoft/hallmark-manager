from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DUserAdmin


from .models import User, Profile

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
