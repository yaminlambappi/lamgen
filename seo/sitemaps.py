"""
Production-grade sitemaps with chunking, dynamic priority, and SEO optimization.

Implements:
- Automatic chunking at 50,000 URLs per Google limit
- Dynamic priority scoring based on page type, freshness, traffic
- Lastmod tracking for efficient crawling
- Section-based sitemap index for crawl budget efficiency
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
import datetime


# Chunk size: Google's limit per sitemap file
SITEMAP_CHUNK_SIZE = getattr(settings, 'SITEMAP_CHUNK_SIZE', 50000)


class SmartPriorityMixin:
    """Mixin to calculate page priority based on multiple signals."""

    def priority(self, obj):
        """Dynamic priority (0-1) with boosts for quality signals."""
        base = getattr(self, 'base_priority', 0.5)
        score = base

        # Freshness boost (updated within last 7 days)
        if hasattr(obj, 'updated_at') and obj.updated_at:
            days = (timezone.now() - obj.updated_at).days
            if days < 7:
                score += 0.15
            elif days < 30:
                score += 0.05

        # Featured boost
        if getattr(obj, 'is_featured', False):
            score += 0.2

        # Traffic boost (if view_count exists and high)
        vc = getattr(obj, 'view_count', 0)
        if vc > 10000:
            score += 0.15
        elif vc > 1000:
            score += 0.1

        # New content boost
        if hasattr(obj, 'created_at') and obj.created_at:
            days = (timezone.now() - obj.created_at).days
            if days < 7:
                score += 0.1

        return min(score, 1.0)


class StaticViewSitemap(Sitemap):
    priority = 1.0  # Homepage highest
    changefreq = 'daily'
    protocol = 'https'

    def items(self):
        return ['home', 'tools:index']

    def location(self, item):
        return reverse(item)


class ToolSitemap(SmartPriorityMixin, Sitemap):
    """Sitemap for tool pages with dynamic priority."""
    changefreq = 'weekly'
    protocol = 'https'
    base_priority = 0.85

    def items(self):
        from tools.models import Tool
        return Tool.objects.filter(is_active=True).select_related('category').order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()

    def priority(self, obj):
        score = super().priority(obj)
        # Tools with high views deserve extra boost
        if obj.view_count > 5000:
            score = min(score + 0.1, 1.0)
        return score


class CategorySitemap(SmartPriorityMixin, Sitemap):
    """Sitemap for category landing pages."""
    changefreq = 'weekly'
    protocol = 'https'
    base_priority = 0.80

    def items(self):
        from tools.models import ToolCategory
        return ToolCategory.objects.filter(is_active=True).order_by('order', 'name')

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        # Use latest tool update in this category
        from tools.models import Tool
        latest = Tool.objects.filter(category=obj, is_active=True).order_by('-updated_at').first()
        return latest.updated_at if latest else timezone.now()


class SEOPageSitemap(SmartPriorityMixin, Sitemap):
    """Sitemap for programmatic SEO content pages."""
    changefreq = 'monthly'
    protocol = 'https'
    base_priority = 0.65

    def items(self):
        from seo.models import SEOPage
        return SEOPage.objects.filter(is_active=True).select_related('category').order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class ToolLongTailSitemap(Sitemap):
    """Long-tail variant pages - lower priority, monthly crawl."""
    priority = 0.55
    changefreq = 'monthly'
    protocol = 'https'

    def items(self):
        from tools.models import LongTailVariant
        return LongTailVariant.objects.filter(is_active=True).select_related('tool__category')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class BlogSitemap(SmartPriorityMixin, Sitemap):
    """Blog/article sitemap with weekly changefreq."""
    changefreq = 'weekly'
    protocol = 'https'
    base_priority = 0.70

    def items(self):
        from blog.models import ContentArticle
        return ContentArticle.objects.filter(is_published=True).order_by('-published_at', '-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


def get_sitemaps():
    """Return ordered dict of sitemap sections for index generation."""
    return {
        'static': StaticViewSitemap,
        'tools': ToolSitemap,
        'categories': CategorySitemap,
        'seo_pages': SEOPageSitemap,
        'longtail': ToolLongTailSitemap,
        'blog': BlogSitemap,
    }
