from django.contrib import admin

from .models import Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):

    list_display = [
        'staff_number',
        'first_name',
        'last_name',
        'email',
        'phone',
        'qualification',
        'admin_enabled',
        'is_admin',
        'is_active',
        'created_at',
    ]

    list_filter = [
        'admin_enabled',
        'is_admin',
        'is_active',
    ]

    search_fields = [
        'staff_number',
        'first_name',
        'last_name',
        'email',
        'phone',
    ]

    readonly_fields = [
        'staff_number',
        'created_at',
        'updated_at',
    ]