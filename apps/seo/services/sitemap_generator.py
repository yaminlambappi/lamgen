"""
Dynamic Sitemap Generation System
Generates comprehensive XML sitemaps for SEO indexing
"""

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Count
from apps.tools.models import Tool, ToolCategory
from apps.seo.models import SEOPage, LongTailVariant
from urllib.parse import urljoin
from django.conf import settings
import datetime
import pytz


class SitemapGenerator:
    """Advanced sitemap generation for comprehensive SEO coverage"""
    
    def __init__(self, request):
        self.request = request
        self.base_url = request.build_absolute_uri('/')
        self.current_time = timezone.now()
        
    def generate_main_sitemap(self) -> str:
        """Generate main sitemap.xml"""
        
        urls = []
        
        # Homepage
        urls.append({
            'loc': self.base_url,
            'lastmod': self.current_time,
            'changefreq': 'daily',
            'priority': '1.0'
        })
        
        # Tools index
        urls.append({
            'loc': urljoin(self.base_url, reverse('tools:index')),
            'lastmod': self._get_latest_tool_update(),
            'changefreq': 'daily',
            'priority': '0.9'
        })
        
        # Workspaces/tools ecosystem
        urls.append({
            'loc': urljoin(self.base_url, reverse('tools:workspaces')),
            'lastmod': self.current_time,
            'changefreq': 'weekly',
            'priority': '0.8'
        })
        
        # Trending tools
        urls.append({
            'loc': urljoin(self.base_url, reverse('tools:trending')),
            'lastmod': self.current_time,
            'changefreq': 'daily',
            'priority': '0.7'
        })
        
        # Category pages
        categories = ToolCategory.objects.filter(is_active=True)
        for category in categories:
            urls.append({
                'loc': urljoin(self.base_url, category.get_absolute_url()),
                'lastmod': self._get_category_lastmod(category),
                'changefreq': 'weekly',
                'priority': '0.8'
            })
        
        return self._render_sitemap(urls)
    
    def generate_tools_sitemap(self) -> str:
        """Generate sitemap for all tools"""
        
        urls = []
        tools = Tool.objects.filter(is_active=True).select_related('category')
        
        for tool in tools:
            urls.append({
                'loc': urljoin(self.base_url, tool.get_absolute_url()),
                'lastmod': tool.updated_at or tool.created_at,
                'changefreq': self._get_tool_changefreq(tool),
                'priority': self._get_tool_priority(tool)
            })
        
        return self._render_sitemap(urls)
    
    def generate_categories_sitemap(self) -> str:
        """Generate sitemap for all categories"""
        
        urls = []
        categories = ToolCategory.objects.filter(is_active=True)
        
        for category in categories:
            urls.append({
                'loc': urljoin(self.base_url, category.get_absolute_url()),
                'lastmod': self._get_category_lastmod(category),
                'changefreq': 'weekly',
                'priority': '0.8'
            })
        
        return self._render_sitemap(urls)
    
    def generate_seo_pages_sitemap(self) -> str:
        """Generate sitemap for SEO programmatic pages"""
        
        urls = []
        seo_pages = SEOPage.objects.filter(is_active=True).select_related('category')
        
        for page in seo_pages:
            urls.append({
                'loc': urljoin(self.base_url, page.get_absolute_url()),
                'lastmod': page.updated_at or page.created_at,
                'changefreq': 'monthly',
                'priority': '0.6'
            })
        
        return self._render_sitemap(urls)
    
    def generate_longtail_sitemap(self) -> str:
        """Generate sitemap for longtail variant pages"""
        
        urls = []
        variants = LongTailVariant.objects.filter(is_active=True).select_related('tool', 'tool__category')
        
        for variant in variants:
            urls.append({
                'loc': urljoin(self.base_url, variant.get_absolute_url()),
                'lastmod': variant.updated_at or variant.created_at,
                'changefreq': 'monthly',
                'priority': '0.5'
            })
        
        return self._render_sitemap(urls)
    
    def generate_image_sitemap(self) -> str:
        """Generate image sitemap"""
        
        urls = []
        
        # Add OG images for tools
        tools = Tool.objects.filter(is_active=True).select_related('category')
        for tool in tools:
            if tool.og_image or True:  # Generate OG image URL even if not stored
                image_url = urljoin(self.base_url, f"/og/{tool.category.slug}/{tool.slug}.png")
                page_url = urljoin(self.base_url, tool.get_absolute_url())
                
                urls.append({
                    'loc': page_url,
                    'images': [{
                        'loc': image_url,
                        'title': tool.name,
                        'caption': tool.short_desc
                    }]
                })
        
        return self._render_image_sitemap(urls)
    
    def generate_sitemap_index(self) -> str:
        """Generate sitemap index file"""
        
        sitemaps = []
        
        # Define all sitemaps
        sitemap_configs = [
            {
                'loc': urljoin(self.base_url, '/sitemap-main.xml'),
                'lastmod': self.current_time
            },
            {
                'loc': urljoin(self.base_url, '/sitemap-tools.xml'),
                'lastmod': self._get_latest_tool_update()
            },
            {
                'loc': urljoin(self.base_url, '/sitemap-categories.xml'),
                'lastmod': self._get_latest_category_update()
            },
            {
                'loc': urljoin(self.base_url, '/sitemap-seo-pages.xml'),
                'lastmod': self._get_latest_seo_page_update()
            },
            {
                'loc': urljoin(self.base_url, '/sitemap-longtail.xml'),
                'lastmod': self._get_latest_longtail_update()
            },
            {
                'loc': urljoin(self.base_url, '/sitemap-images.xml'),
                'lastmod': self.current_time
            }
        ]
        
        for config in sitemap_configs:
            sitemaps.append(config)
        
        return self._render_sitemap_index(sitemaps)
    
    def _render_sitemap(self, urls: list) -> str:
        """Render sitemap XML"""
        
        context = {
            'urls': urls,
            'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'
        }
        
        return render_to_string('seo/sitemap.xml', context)
    
    def _render_image_sitemap(self, urls: list) -> str:
        """Render image sitemap XML"""
        
        context = {
            'urls': urls,
            'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'xmlns_image': 'http://www.google.com/schemas/sitemap-image/1.1'
        }
        
        return render_to_string('seo/image_sitemap.xml', context)
    
    def _render_sitemap_index(self, sitemaps: list) -> str:
        """Render sitemap index XML"""
        
        context = {
            'sitemaps': sitemaps,
            'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9'
        }
        
        return render_to_string('seo/sitemap_index.xml', context)
    
    def _get_tool_changefreq(self, tool: Tool) -> str:
        """Determine change frequency for tool"""
        
        if tool.is_new:
            return 'daily'
        elif tool.is_featured:
            return 'weekly'
        elif tool.view_count > 1000:
            return 'monthly'
        else:
            return 'monthly'
    
    def _get_tool_priority(self, tool: Tool) -> str:
        """Calculate priority for tool"""
        
        if tool.is_featured:
            return '0.9'
        elif tool.is_new:
            return '0.8'
        elif tool.view_count > 1000:
            return '0.7'
        elif tool.view_count > 100:
            return '0.6'
        else:
            return '0.5'
    
    def _get_category_lastmod(self, category: ToolCategory) -> datetime.datetime:
        """Get last modification date for category"""
        
        latest_tool = category.tools.filter(is_active=True).order_by('-updated_at').first()
        if latest_tool:
            return latest_tool.updated_at or latest_tool.created_at
        
        return category.updated_at or category.created_at
    
    def _get_latest_tool_update(self) -> datetime.datetime:
        """Get latest tool update across all tools"""
        
        latest_tool = Tool.objects.filter(is_active=True).order_by('-updated_at').first()
        if latest_tool:
            return latest_tool.updated_at or latest_tool.created_at
        
        return self.current_time
    
    def _get_latest_category_update(self) -> datetime.datetime:
        """Get latest category update"""
        
        latest_category = ToolCategory.objects.filter(is_active=True).order_by('-updated_at').first()
        if latest_category:
            return latest_category.updated_at or latest_category.created_at
        
        return self.current_time
    
    def _get_latest_seo_page_update(self) -> datetime.datetime:
        """Get latest SEO page update"""
        
        latest_page = SEOPage.objects.filter(is_active=True).order_by('-updated_at').first()
        if latest_page:
            return latest_page.updated_at or latest_page.created_at
        
        return self.current_time
    
    def _get_latest_longtail_update(self) -> datetime.datetime:
        """Get latest longtail variant update"""
        
        latest_variant = LongTailVariant.objects.filter(is_active=True).order_by('-updated_at').first()
        if latest_variant:
            return latest_variant.updated_at or latest_variant.created_at
        
        return self.current_time
    
    def get_sitemap_statistics(self) -> dict:
        """Get comprehensive sitemap statistics"""
        
        stats = {
            'total_urls': 0,
            'tool_count': Tool.objects.filter(is_active=True).count(),
            'category_count': ToolCategory.objects.filter(is_active=True).count(),
            'seo_page_count': SEOPage.objects.filter(is_active=True).count(),
            'longtail_count': LongTailVariant.objects.filter(is_active=True).count(),
            'image_count': 0,
            'last_updated': self.current_time,
            'sitemap_files': []
        }
        
        # Count URLs in each sitemap
        stats['sitemap_files'] = [
            {
                'name': 'sitemap-main.xml',
                'url_count': len(self._get_main_sitemap_urls()),
                'priority': 'high'
            },
            {
                'name': 'sitemap-tools.xml',
                'url_count': stats['tool_count'],
                'priority': 'high'
            },
            {
                'name': 'sitemap-categories.xml',
                'url_count': stats['category_count'],
                'priority': 'medium'
            },
            {
                'name': 'sitemap-seo-pages.xml',
                'url_count': stats['seo_page_count'],
                'priority': 'medium'
            },
            {
                'name': 'sitemap-longtail.xml',
                'url_count': stats['longtail_count'],
                'priority': 'low'
            },
            {
                'name': 'sitemap-images.xml',
                'url_count': stats['tool_count'],  # One image per tool
                'priority': 'low'
            }
        ]
        
        stats['total_urls'] = sum(file['url_count'] for file in stats['sitemap_files'])
        stats['image_count'] = stats['tool_count']
        
        return stats
    
    def _get_main_sitemap_urls(self) -> list:
        """Get URLs for main sitemap"""
        
        urls = []
        
        # Homepage
        urls.append(self.base_url)
        
        # Tools index
        urls.append(urljoin(self.base_url, reverse('tools:index')))
        
        # Workspaces
        urls.append(urljoin(self.base_url, reverse('tools:workspaces')))
        
        # Trending
        urls.append(urljoin(self.base_url, reverse('tools:trending')))
        
        # Categories
        categories = ToolCategory.objects.filter(is_active=True)
        for category in categories:
            urls.append(urljoin(self.base_url, category.get_absolute_url()))
        
        return urls
    
    def ping_search_engines(self) -> dict:
        """Ping search engines with updated sitemaps"""
        
        sitemap_url = urljoin(self.base_url, '/sitemap.xml')
        
        # Search engine ping URLs
        ping_urls = {
            'google': f'https://www.google.com/webmasters/tools/ping?sitemap={sitemap_url}',
            'bing': f'https://www.bing.com/webmaster/ping.aspx?siteMap={sitemap_url}',
            'yandex': f'https://webmaster.yandex.ru/ping?sitemap={sitemap_url}'
        }
        
        results = {}
        
        # Note: In production, you would make actual HTTP requests here
        # For now, we'll just return the URLs that would be pinged
        
        for engine, ping_url in ping_urls.items():
            results[engine] = {
                'ping_url': ping_url,
                'status': 'ready_to_ping',
                'sitemap_url': sitemap_url
            }
        
        return results
    
    def validate_sitemap_coverage(self) -> dict:
        """Validate sitemap coverage and identify gaps"""
        
        validation = {
            'total_indexable_items': 0,
            'sitemap_coverage': 0,
            'missing_items': [],
            'orphaned_pages': [],
            'recommendations': []
        }
        
        # Count all indexable items
        tool_count = Tool.objects.filter(is_active=True).count()
        category_count = ToolCategory.objects.filter(is_active=True).count()
        seo_page_count = SEOPage.objects.filter(is_active=True).count()
        longtail_count = LongTailVariant.objects.filter(is_active=True).count()
        
        validation['total_indexable_items'] = tool_count + category_count + seo_page_count + longtail_count
        
        # Count sitemap URLs
        stats = self.get_sitemap_statistics()
        sitemap_url_count = stats['total_urls'] - 6  # Subtract non-content URLs
        
        validation['sitemap_coverage'] = sitemap_url_count
        coverage_percentage = (sitemap_url_count / validation['total_indexable_items']) * 100 if validation['total_indexable_items'] > 0 else 0
        
        # Identify missing items
        if coverage_percentage < 95:
            validation['missing_items'].append({
                'type': 'coverage_gap',
                'percentage': coverage_percentage,
                'message': f'Sitemap covers only {coverage_percentage:.1f}% of indexable content'
            })
        
        # Check for orphaned pages (pages without internal links)
        tools_with_no_links = Tool.objects.filter(is_active=True).filter(
            Q(seo_intro='') | Q(use_cases=[]) | Q(faq_items=[])
        ).count()
        
        if tools_with_no_links > 0:
            validation['orphaned_pages'].append({
                'type': 'tools_without_seo_content',
                'count': tools_with_no_links,
                'message': f'{tools_with_no_links} tools lack comprehensive SEO content'
            })
        
        # Generate recommendations
        if coverage_percentage < 100:
            validation['recommendations'].append('Ensure all indexable content is included in sitemaps')
        
        if tools_with_no_links > 0:
            validation['recommendations'].append('Generate SEO content for all tools to improve internal linking')
        
        if stats['seo_page_count'] < tool_count * 2:
            validation['recommendations'].append('Create more programmatic SEO pages for long-tail coverage')
        
        return validation
    
    def generate_robots_txt(self) -> str:
        """Generate comprehensive robots.txt"""
        
        robots_content = f"""# robots.txt for LamGen
# Generated on {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}

User-agent: *
Allow: /

# Sitemaps
Sitemap: {urljoin(self.base_url, '/sitemap.xml')}

# Crawl-delay for respectful crawling
Crawl-delay: 1

# Disallow temporary/admin pages
Disallow: /admin/
Disallow: /api/
Disallow: /static/
Disallow: /media/

# Allow specific important paths
Allow: /tools/
Allow: /seo/
Allow: /guides/

# Special instructions for major search engines
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Slurp
Allow: /
"""
        
        return robots_content


# Helper functions for views
def generate_sitemap_response(sitemap_type: str, request) -> HttpResponse:
    """Generate sitemap response for given type"""
    
    generator = SitemapGenerator(request)
    
    sitemap_methods = {
        'main': generator.generate_main_sitemap,
        'tools': generator.generate_tools_sitemap,
        'categories': generator.generate_categories_sitemap,
        'seo-pages': generator.generate_seo_pages_sitemap,
        'longtail': generator.generate_longtail_sitemap,
        'images': generator.generate_image_sitemap,
        'index': generator.generate_sitemap_index
    }
    
    if sitemap_type not in sitemap_methods:
        return HttpResponse('Sitemap not found', status=404)
    
    sitemap_content = sitemap_methods[sitemap_type]()
    
    response = HttpResponse(sitemap_content, content_type='application/xml')
    response['Content-Type'] = 'application/xml; charset=utf-8'
    
    # Add caching headers
    response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
    
    return response


def generate_robots_txt_response(request) -> HttpResponse:
    """Generate robots.txt response"""
    
    generator = SitemapGenerator(request)
    robots_content = generator.generate_robots_txt()
    
    response = HttpResponse(robots_content, content_type='text/plain')
    response['Cache-Control'] = 'public, max-age=86400'  # Cache for 24 hours
    
    return response
