from django.contrib import admin

from .models import ThesisChunk, ThesisRequest


def mark_as_failed(modeladmin, request, queryset):
    queryset.update(status='FAILED')


mark_as_failed.short_description = 'Mark selected thesis requests as FAILED'


@admin.register(ThesisRequest)
class ThesisRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    actions = [mark_as_failed, 'delete_selected']
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ThesisChunk)
class ThesisChunkAdmin(admin.ModelAdmin):
    list_display = ['id', 'thesis_request', 'order', 'token_count']
    list_filter = ['thesis_request__status']
    search_fields = ['thesis_request__title']
    ordering = ['thesis_request', 'order']
