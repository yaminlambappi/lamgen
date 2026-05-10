"""
Production-grade sitemap engine with chunking, index, auto-ping, and intelligent priority.

Features:
- Automatic sitemap chunking at 50,000 URLs (Google limit)
- Sitemap index with proper priority/changefreq per section
- Auto-ping search engines on content publish
- Smart priority based on page type, traffic, and freshness
- Supports tools, categories, blog, SEO pages, longtail variants
- Redis-backed cache for performance
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.conf import settings
from django.db.models import Count, F
from typing import Optional, List, Dict, Any
import datetime
import hashlib


class ChunkedSitemapMixin:
    """Mixin to automatically chunk large sitemaps at 50k URL limit."""
    CHUNK_SIZE = 50000  # Google's sitemap limit
    
    def items(self):
        """Override to return all items. Base class returns flat queryset."""
        return super().items()
    
    def get_chunked_items(self):
        """Generator that yields chunks of items."""
        items = list(self.items())
        for i in range(0, len(items), self.CHUNK_SIZE):
            yield items[i:i + self.CHUNK_SIZE]
    
    @property
    def chunk_count(self):
        return (len(list(self.items())) + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE


class SmartPriorityMixin:
    """Mixin to calculate page priority based on multiple signals."""
    
    def priority(self, obj):
        """Dynamic priority based on page type and signals."""
        base_priority = getattr(super(), 'priority', None)
        if base_priority and callable(base_priority):
            return base_priority(obj)
        
        # Default dynamic priority calculation
        return self._calculate_priority(obj)
    
    def _calculate_priority(self, obj):
        """Calculate intelligent priority score (0-1)."""
        score = 0.5  # Base
        
        # Boost for featured content
        if hasattr(obj, 'is_featured') and obj.is_featured:
            score += 0.2
        
        # Boost for recent updates (within 7 days)
        if hasattr(obj, 'updated_at') and obj.updated_at:
            days_old = (datetime.datetime.now(datetime.timezone.utc) - obj.updated_at).days
            if days_old < 7:
                score += 0.15
            elif days_old < 30:
                score += 0.05
        
        # Boost for high traffic (if view_count exists)
        if hasattr(obj, 'view_count'):
            if obj.view_count > 10000:
                score += 0.15
            elif obj.view_count > 1000:
                score += 0.1
        
        # Cap at 1.0
        return min(score, 1.0)


class ToolSitemap(SmartPriorityMixin, ChunkedSitemapMixin, Sitemap):
    """Sitemap for tools with chunking support."""
    changefreq = 'weekly'
    protocol = 'https'
    
    def items(self):
        from tools.models import Tool
        return list(
            Tool.objects.filter(is_active=True)
            .select_related('category')
            .only('id', 'slug', 'updated_at', 'is_featured', 'view_count')
            .order_by('-updated_at')
        )
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()
    
    def priority(self, obj):
        score = 0.80  # Tool pages are important
        
        if obj.is_featured:
            score += 0.15
        
        if obj.updated_at:
            days_old = (datetime.datetime.now(datetime.timezone.utc) - obj.updated_at).days
            if days_old < 7:
                score += 0.1
            elif days_old < 30:
                score += 0.05
        
        if hasattr(obj, 'view_count') and obj.view_count > 5000:
            score += 0.1
            
        return min(score, 1.0)
    
    def get_chunked_items(self):
        """Override to return actual chunking."""
        items = list(self.items())
        chunk_size = getattr(settings, 'SITEMAP_CHUNK_SIZE', 50000)
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]


class CategorySitemap(SmartPriorityMixin, Sitemap):
    """Sitemap for category landing pages."""
    priority = 0.75
    changefreq = 'weekly'
    protocol = 'https'
    
    def items(self):
        from tools.models import ToolCategory
        return list(
            ToolCategory.objects.filter(is_active=True)
            .annotate(tool_count=Count('tools'))
            .order_by('order', 'name')
        )
    
    def lastmod(self, obj):
        # Use latest tool update in category
        from tools.models import Tool
        import datetime
        latest = Tool.objects.filter(category=obj, is_active=True).order_by('-updated_at').first()
        if latest:
            return latest.updated_at
        # Fallback to a fixed date rather than obj.pk (which is an int, not a date)
        return datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    
    def location(self, obj):
        return obj.get_absolute_url()


class ToolLongTailSitemap(SmartPriorityMixin, Sitemap):
    """Sitemap for longtail variant pages (lower priority)."""
    priority = 0.60
    changefreq = 'monthly'
    protocol = 'https'
    
    def items(self):
        from seo.models import LongTailVariant
        return list(
            LongTailVariant.objects.filter(is_active=True)
            .select_related('tool__category')
            .order_by('-updated_at')
        )
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        # Longtail variants canonicalize to main tool URL
        # but we still serve separate pages with unique content
        return obj.get_absolute_url()


class SEOSitemap(SmartPriorityMixin, Sitemap):
    """Sitemap for programmatic SEO pages."""
    priority = 0.65
    changefreq = 'monthly'
    protocol = 'https'
    
    def items(self):
        from seo.models import SEOPage
        return list(
            SEOPage.objects.filter(is_active=True)
            .select_related('category')
            .order_by('-updated_at')
        )
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()


class BlogSitemap(SmartPriorityMixin, Sitemap):
    """Sitemap for blog articles."""
    priority = 0.70
    changefreq = 'weekly'
    protocol = 'https'
    
    def items(self):
        from blog.models import ContentArticle
        return list(
            ContentArticle.objects.filter(is_published=True)
            .order_by('-published_at', '-updated_at')
        )
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()


class StaticViewSitemap(SmartPriorityMixin, Sitemap):
    """Sitemap for static pages (home, trending, etc.)."""
    priority = 1.0  # Highest for homepage
    changefreq = 'daily'
    protocol = 'https'
    
    def items(self):
        return ['home', 'tools:index', 'tools:trending']
    
    def location(self, item):
        from django.urls import reverse
        return reverse(item)


def get_sitemap_sections():
    """Return ordered dict of sitemap sections for index generation."""
    return {
        'static': StaticViewSitemap,
        'tools': ToolSitemap,
        'categories': CategorySitemap,
        'longtail': ToolLongTailSitemap,
        'seo_pages': SEOSitemap,
        'blog': BlogSitemap,
    }


def ping_search_engines():
    """Ping search engines after sitemap update."""
    import requests
    
    sitemap_url = f"{settings.SITE_URL}/sitemap.xml"
    
    search_engines = [
        f"https://www.google.com/ping?sitemap={sitemap_url}",
        f"https://www.bing.com/ping?sitemap={sitemap_url}",
    ]
    
    results = []
    for url in search_engines:
        try:
            resp = requests.get(url, timeout=5)
            results.append({'url': url, 'status': resp.status_code, 'ok': resp.ok})
        except Exception as e:
            results.append({'url': url, 'error': str(e), 'ok': False})
    
    return results


def rebuild_all_sitemaps():
    """Force rebuild all sitemaps (used after bulk content changes)."""
    from django.core.cache import cache
    from django.contrib.sitemaps import views as sitemap_views
    
    # Clear sitemap cache
    cache.delete_pattern('sitemap_*')
    
    # Pre-warm sitemaps by accessing each
    sections = get_sitemap_sections()
    for section_name, sitemap_class in sections.items():
        sitemap = sitemap_class()
        # Force items evaluation
        _ = list(sitemap.items())
    
    # Ping search engines
    ping_results = ping_search_engines()
    
    return {
        'sections': list(sections.keys()),
        'ping_results': ping_results,
        'message': 'Sitemaps rebuilt and search engines notified'
    }
