from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class KipasUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'is_email_verified', 'is_staff', 'created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('KIPAS', {'fields': ('is_email_verified', 'is_deactivated', 'two_factor_enabled')}),
    )
