from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('university', 'bio')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile', {'fields': ('email', 'university', 'bio')}),
    )
    list_display = ['username', 'email', 'university', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'university']
