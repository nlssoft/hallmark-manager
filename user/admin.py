from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DUserAdmin


from .models import User

#need to think about what to do???
from django.contrib.auth.models import Group
from django.contrib.admin.sites import NotRegistered

@admin.register(User)
class UserAdmin(DUserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'phone_number',
        'company_name',
        'company_address',
        'parent',
        'is_staff',
        'is_active',
    )

    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'phone_number',
        'company_name',
    )

    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
    )

    fieldsets= (
        (None, {
            'fields': ('username', 'password'),
        }),
        ('Personal info', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'phone_number',
                'address',
            ),
        }),
        ('Company info', {
            'fields': (
                'company_name',
                'company_address',
                'parent',
            ),
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
            ),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'phone_number',
                'address',
                'password1',
                'password2',
                'is_active',
                'is_staff',
                'is_superuser',
            ),
        }),
    )