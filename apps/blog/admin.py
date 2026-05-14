from django.contrib import admin
from .models import ContentArticle


@admin.register(ContentArticle)
class ContentArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "content_type", "is_published", "published_at", "updated_at"]
    list_filter = ["content_type", "is_published"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ["related_tools"]
    date_hierarchy = "published_at"
