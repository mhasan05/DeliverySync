from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from account.models import UserAuth


class CustomUserAdmin(UserAdmin):
    model = UserAuth
    list_display = ('email', 'name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    ordering = ('email',)
    search_fields = ('email', 'name')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name', 'image', 'phone_number', 'address')}),
        ('Delivery Fee', {'fields': ('default_delivery_fee',)}),
        ('Location', {'fields': ('location_latitude', 'location_longitude')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Driver Info', {'fields': ('vehicle', 'vehicle_registration_number', 'driving_license_number')}),
        ('Account Info', {'fields': ('account_balance', 'date_joined')}),
        ('OTP', {'fields': ('otp', 'otp_expired')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password1', 'password2', 'is_active', 'is_staff')
        }),
    )


admin.site.register(UserAuth, CustomUserAdmin)
admin.site.unregister(Group)
