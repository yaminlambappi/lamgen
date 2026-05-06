from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from tools.models import Tool, ToolCategory
from seo.models import SEOPage, SEOCategory


class StaticViewSitemap(Sitemap):
    """Sitemap for static/homepage views."""
    priority = 1.0
    changefreq = 'daily'
    protocol = 'https'

    def items(self):
        return ['home', 'tools:index']

    def location(self, item):
        return reverse(item)


class ToolSitemap(Sitemap):
    priority = 0.85
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return Tool.objects.filter(is_active=True).select_related('category').order_by('-view_count')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()

    def priority(self, obj):
        # Boost priority for featured and high-traffic tools
        if obj.is_featured:
            return 0.95
        if obj.view_count > 1000:
            return 0.90
        if obj.view_count > 100:
            return 0.85
        return 0.75


class CategorySitemap(Sitemap):
    priority = 0.80
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return ToolCategory.objects.filter(is_active=True).order_by('order')

    def location(self, obj):
        return obj.get_absolute_url()


class SEOPageSitemap(Sitemap):
    priority = 0.60
    changefreq = 'monthly'
    protocol = 'https'

    def items(self):
        return SEOPage.objects.filter(is_active=True).select_related('category')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
