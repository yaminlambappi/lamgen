from django.contrib import admin
from .models import ToolCategory, Tool, ToolBookmark, ToolUsageHistory


@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'is_featured', 'is_new', 'view_count', 'order']
    list_editable = ['is_active', 'is_featured', 'is_new', 'order']
    list_filter = ['category', 'is_active', 'is_featured', 'is_new', 'is_pro']
    search_fields = ['name', 'description', 'tags']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['view_count', 'created_at', 'updated_at']


@admin.register(ToolBookmark)
class ToolBookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'tool', 'created_at']
    list_filter = ['tool__category']
    search_fields = ['user__username', 'tool__name']


@admin.register(ToolUsageHistory)
class ToolUsageHistoryAdmin(admin.ModelAdmin):
    list_display = ['tool', 'user', 'session_key', 'used_at']
    list_filter = ['tool__category']
    search_fields = ['tool__name', 'user__username']
