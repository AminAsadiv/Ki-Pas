from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'city', 'level', 'xp', 'is_verified_host']
    list_filter = ['is_verified_host', 'level', 'is_public']
    search_fields = ['user__username', 'full_name', 'city']
