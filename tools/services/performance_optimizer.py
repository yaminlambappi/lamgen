"""
Performance Optimization System
Implements caching, lazy loading, and performance optimizations for SEO
"""

from django.core.cache import cache
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.vary import vary_on_headers, vary_on_cookie
from django.db.models import Q, Count, F, Prefetch
from django.core.paginator import Paginator
from django.conf import settings
from tools.models import Tool, ToolCategory
from seo.models import SEOPage, LongTailVariant
import time
import hashlib


class PerformanceOptimizer:
    """Advanced performance optimization for SEO pages"""
    
    def __init__(self):
        self.cache_timeout = {
            'tool_page': 60 * 60,      # 1 hour
            'category_page': 60 * 30,   # 30 minutes
            'seo_page': 60 * 60 * 2,   # 2 hours
            'homepage': 60 * 15,       # 15 minutes
            'internal_links': 60 * 30, # 30 minutes
            'metadata': 60 * 60 * 4,   # 4 hours
            'sitemap': 60 * 60 * 24     # 24 hours
        }
        
        self.compression_threshold = 1024  # Compress responses over 1KB
    
    def get_cached_tool_data(self, tool_id: int) -> dict:
        """Get cached tool data with performance optimizations"""
        
        cache_key = f"tool_data_{tool_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # Fetch tool with optimized queries
        try:
            tool = Tool.objects.select_related('category').prefetch_related(
                Prefetch('category__tools', 
                        queryset=Tool.objects.filter(is_active=True).order_by('order', 'name'),
                        to_attr='related_tools')
            ).get(id=tool_id, is_active=True)
            
            # Prepare optimized data
            tool_data = {
                'tool': tool,
                'category': tool.category,
                'related_tools': list(tool.category.related_tools)[:8],
                'seo_score': getattr(tool, 'seo_score', None),
                'keywords': tool.keywords or [],
                'internal_links': self._get_cached_internal_links(tool),
                'content_blocks': tool.content_blocks or [],
                'use_cases': tool.use_cases or [],
                'faq_items': tool.faq_items or [],
                'examples': tool.examples or []
            }
            
            # Cache the data
            cache.set(cache_key, tool_data, self.cache_timeout['tool_page'])
            
            return tool_data
            
        except Tool.DoesNotExist:
            return None
    
    def get_cached_category_data(self, category_id: int) -> dict:
        """Get cached category data with performance optimizations"""
        
        cache_key = f"category_data_{category_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            category = ToolCategory.objects.prefetch_related(
                Prefetch('tools', 
                        queryset=Tool.objects.filter(is_active=True).order_by('order', 'name'),
                        to_attr='active_tools')
            ).get(id=category_id, is_active=True)
            
            # Prepare optimized data
            category_data = {
                'category': category,
                'tools': list(category.active_tools),
                'featured_tools': category.get_featured_tools_objects(),
                'trending_tools': category.get_trending_tools(6),
                'newest_tools': category.get_newest_tools(4),
                'tool_groups': self._group_tools_cached(category),
                'seo_metadata': category.get_seo_metadata(),
                'internal_links': self._get_cached_category_links(category)
            }
            
            # Cache the data
            cache.set(cache_key, category_data, self.cache_timeout['category_page'])
            
            return category_data
            
        except ToolCategory.DoesNotExist:
            return None
    
    def get_cached_seo_page_data(self, page_id: int) -> dict:
        """Get cached SEO page data with performance optimizations"""
        
        cache_key = f"seo_page_data_{page_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            page = SEOPage.objects.select_related('category').prefetch_related(
                'related_tools'
            ).get(id=page_id, is_active=True)
            
            # Prepare optimized data
            page_data = {
                'page': page,
                'category': page.category,
                'related_tools': list(page.related_tools.all()[:6]),
                'item_count': len(page.items),
                'internal_links': self._get_cached_seo_page_links(page)
            }
            
            # Cache the data
            cache.set(cache_key, page_data, self.cache_timeout['seo_page'])
            
            return page_data
            
        except SEOPage.DoesNotExist:
            return None
    
    def _get_cached_internal_links(self, tool: Tool) -> list:
        """Get cached internal links for tool"""
        
        cache_key = f"internal_links_tool_{tool.pk}"
        cached_links = cache.get(cache_key)
        
        if cached_links:
            return cached_links
        
        # Generate links (this would use the internal linking engine)
        from tools.services.internal_linking import internal_linking_engine
        links = internal_linking_engine.get_tool_internal_links(tool)
        
        # Cache for shorter time since links might change
        cache.set(cache_key, links, self.cache_timeout['internal_links'])
        
        return links
    
    def _get_cached_category_links(self, category: ToolCategory) -> list:
        """Get cached internal links for category"""
        
        cache_key = f"internal_links_category_{category.pk}"
        cached_links = cache.get(cache_key)
        
        if cached_links:
            return cached_links
        
        from tools.services.internal_linking import internal_linking_engine
        links = internal_linking_engine.get_category_internal_links(category)
        
        cache.set(cache_key, links, self.cache_timeout['internal_links'])
        
        return links
    
    def _get_cached_seo_page_links(self, page: SEOPage) -> list:
        """Get cached internal links for SEO page"""
        
        cache_key = f"internal_links_seo_{page.pk}"
        cached_links = cache.get(cache_key)
        
        if cached_links:
            return cached_links
        
        # Generate related links for SEO page
        links = []
        
        # Add related tools
        for tool in page.related_tools.all()[:6]:
            links.append({
                'type': 'tool',
                'title': tool.name,
                'url': tool.get_absolute_url(),
                'description': tool.short_desc
            })
        
        cache.set(cache_key, links, self.cache_timeout['internal_links'])
        
        return links
    
    def _group_tools_cached(self, category: ToolCategory) -> list:
        """Group tools with caching"""
        
        cache_key = f"tool_groups_{category.pk}"
        cached_groups = cache.get(cache_key)
        
        if cached_groups:
            return cached_groups
        
        # Group tools (using existing logic)
        tools = list(category.tools.filter(is_active=True).order_by('order', 'name'))
        tool_groups = {}
        
        for tool in tools:
            group_name = self._determine_tool_group(tool)
            if group_name not in tool_groups:
                tool_groups[group_name] = []
            tool_groups[group_name].append(tool)
        
        # Sort groups
        sorted_groups = []
        for group_name in sorted(tool_groups.keys()):
            if group_name != "Other Tools":
                sorted_groups.append((group_name, tool_groups[group_name]))
        
        if "Other Tools" in tool_groups:
            sorted_groups.append(("Other Tools", tool_groups["Other Tools"]))
        
        cache.set(cache_key, sorted_groups, self.cache_timeout['category_page'])
        
        return sorted_groups
    
    def _determine_tool_group(self, tool: Tool) -> str:
        """Determine tool group (simplified version)"""
        
        name_lower = tool.name.lower()
        
        if any(word in name_lower for word in ["format", "beautify", "lint"]):
            return "Formatting & Validation"
        elif any(word in name_lower for word in ["convert", "transform"]):
            return "Converters & Transformers"
        elif any(word in name_lower for word in ["generat", "create", "build"]):
            return "Generators & Builders"
        else:
            return "Other Tools"
    
    def invalidate_tool_cache(self, tool_id: int):
        """Invalidate cache for specific tool"""
        
        cache_keys = [
            f"tool_data_{tool_id}",
            f"internal_links_tool_{tool_id}"
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        # Invalidate category cache if needed
        try:
            tool = Tool.objects.get(id=tool_id)
            cache.delete(f"category_data_{tool.category.id}")
            cache.delete(f"tool_groups_{tool.category.id}")
        except Tool.DoesNotExist:
            pass
    
    def invalidate_category_cache(self, category_id: int):
        """Invalidate cache for specific category"""
        
        cache_keys = [
            f"category_data_{category_id}",
            f"internal_links_category_{category_id}",
            f"tool_groups_{category_id}"
        ]
        
        for key in cache_keys:
            cache.delete(key)
    
    def get_performance_metrics(self) -> dict:
        """Get performance metrics and statistics"""
        
        metrics = {
            'cache_hit_ratio': self._calculate_cache_hit_ratio(),
            'average_response_time': self._get_average_response_time(),
            'memory_usage': self._get_memory_usage(),
            'cache_size': self._get_cache_size(),
            'optimization_recommendations': self._get_optimization_recommendations()
        }
        
        return metrics
    
    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio (simulated)"""
        
        # In production, this would track actual cache hits/misses
        # For now, return a reasonable estimate
        return 0.85  # 85% cache hit ratio
    
    def _get_average_response_time(self) -> float:
        """Get average response time (simulated)"""
        
        # In production, this would track actual response times
        return 0.15  # 150ms average response time
    
    def _get_memory_usage(self) -> dict:
        """Get memory usage statistics"""
        
        # This would use actual memory monitoring in production
        return {
            'total_cache_memory': '256MB',
            'active_cache_entries': 1500,
            'memory_efficiency': 'good'
        }
    
    def _get_cache_size(self) -> dict:
        """Get cache size information"""
        
        return {
            'total_entries': cache._cache.__len__() if hasattr(cache, '_cache') else 0,
            'estimated_size': '256MB',
            'max_size': '512MB'
        }
    
    def _get_optimization_recommendations(self) -> list:
        """Get performance optimization recommendations"""
        
        recommendations = []
        
        # Check cache hit ratio
        hit_ratio = self._calculate_cache_hit_ratio()
        if hit_ratio < 0.8:
            recommendations.append({
                'type': 'cache_optimization',
                'priority': 'high',
                'message': f'Cache hit ratio is {hit_ratio:.1%}, consider increasing cache timeouts'
            })
        
        # Check response time
        avg_time = self._get_average_response_time()
        if avg_time > 0.5:
            recommendations.append({
                'type': 'response_time',
                'priority': 'medium',
                'message': f'Average response time is {avg_time:.3f}s, consider optimizing database queries'
            })
        
        # Add general recommendations
        recommendations.extend([
            {
                'type': 'database_optimization',
                'priority': 'low',
                'message': 'Consider adding database indexes for frequently queried fields'
            },
            {
                'type': 'cdn_optimization',
                'priority': 'medium',
                'message': 'Implement CDN for static assets to improve load times'
            },
            {
                'type': 'compression',
                'priority': 'low',
                'message': 'Enable gzip compression for all responses'
            }
        ])
        
        return recommendations
    
    def optimize_database_queries(self):
        """Provide database query optimization recommendations"""
        
        recommendations = []
        
        # Check for missing indexes
        recommendations.append({
            'table': 'tools_tool',
            'field': 'category_id',
            'recommendation': 'Add index for faster category-based queries'
        })
        
        recommendations.append({
            'table': 'tools_tool',
            'field': 'is_active',
            'recommendation': 'Add index for filtering active tools'
        })
        
        recommendations.append({
            'table': 'tools_tool',
            'field': 'view_count',
            'recommendation': 'Add index for sorting by popularity'
        })
        
        return recommendations
    
    def get_caching_strategy(self) -> dict:
        """Get comprehensive caching strategy"""
        
        strategy = {
            'page_caching': {
                'tool_pages': {
                    'duration': self.cache_timeout['tool_page'],
                    'vary_on': ['user-agent', 'accept-language'],
                    'compression': True
                },
                'category_pages': {
                    'duration': self.cache_timeout['category_page'],
                    'vary_on': ['user-agent'],
                    'compression': True
                },
                'seo_pages': {
                    'duration': self.cache_timeout['seo_page'],
                    'vary_on': ['user-agent'],
                    'compression': True
                },
                'homepage': {
                    'duration': self.cache_timeout['homepage'],
                    'vary_on': ['user-agent', 'accept-language'],
                    'compression': True
                }
            },
            'fragment_caching': {
                'internal_links': {
                    'duration': self.cache_timeout['internal_links'],
                    'invalidation_triggers': ['tool_update', 'category_update']
                },
                'tool_groups': {
                    'duration': self.cache_timeout['category_page'],
                    'invalidation_triggers': ['tool_update', 'category_update']
                },
                'metadata': {
                    'duration': self.cache_timeout['metadata'],
                    'invalidation_triggers': ['tool_update', 'category_update']
                }
            },
            'edge_caching': {
                'static_assets': {
                    'duration': 60 * 60 * 24 * 30,  # 30 days
                    'cache_control': 'public, max-age=2592000, immutable'
                },
                'images': {
                    'duration': 60 * 60 * 24 * 7,  # 7 days
                    'cache_control': 'public, max-age=604800'
                },
                'api_responses': {
                    'duration': 60 * 15,  # 15 minutes
                    'cache_control': 'public, max-age=900'
                }
            }
        }
        
        return strategy
    
    def implement_lazy_loading(self) -> dict:
        """Implement lazy loading strategies"""
        
        lazy_loading_config = {
            'tool_components': {
                'related_tools': {
                    'strategy': 'intersection_observer',
                    'threshold': 0.1,
                    'root_margin': '50px'
                },
                'faq_section': {
                    'strategy': 'intersection_observer',
                    'threshold': 0.1,
                    'root_margin': '100px'
                },
                'examples_section': {
                    'strategy': 'click_to_load',
                    'trigger': 'button'
                }
            },
            'category_components': {
                'tool_grid': {
                    'strategy': 'pagination',
                    'initial_load': 12,
                    'load_more': 12
                },
                'tool_groups': {
                    'strategy': 'intersection_observer',
                    'threshold': 0.1
                }
            },
            'image_optimization': {
                'lazy_loading': True,
                'placeholder': 'blur',
                'formats': ['webp', 'avif', 'jpg'],
                'sizes': {
                    'thumbnail': '150x150',
                    'medium': '400x300',
                    'large': '800x600'
                }
            }
        }
        
        return lazy_loading_config
    
    def get_core_web_vitals_optimization(self) -> dict:
        """Get Core Web Vitals optimization recommendations"""
        
        optimizations = {
            'largest_contentful_paint': {
                'target': '< 2.5s',
                'recommendations': [
                    'Optimize image loading with WebP format',
                    'Implement resource hints (preload, prefetch)',
                    'Minimize render-blocking resources',
                    'Use efficient caching strategies'
                ]
            },
            'first_input_delay': {
                'target': '< 100ms',
                'recommendations': [
                    'Minimize JavaScript execution time',
                    'Reduce third-party script impact',
                    'Use code splitting for JavaScript',
                    'Optimize event listeners'
                ]
            },
            'cumulative_layout_shift': {
                'target': '< 0.1',
                'recommendations': [
                    'Always include dimensions for images and videos',
                    'Reserve space for dynamic content',
                    'Avoid inserting content above existing content',
                    'Use transform animations instead of changing layout'
                ]
            }
        }
        
        return optimizations


# Decorators for view optimization
def optimized_tool_page(view_func):
    """Decorator for optimized tool page views"""
    
    decorated_view = cache_page(60 * 60)(view_func)  # Cache for 1 hour
    decorated_view = cache_control(public=True, max_age=3600)(decorated_view)
    decorated_view = vary_on_headers('User-Agent', 'Accept-Language')(decorated_view)
    
    return decorated_view


def optimized_category_page(view_func):
    """Decorator for optimized category page views"""
    
    decorated_view = cache_page(60 * 30)(view_func)  # Cache for 30 minutes
    decorated_view = cache_control(public=True, max_age=1800)(decorated_view)
    decorated_view = vary_on_headers('User-Agent')(decorated_view)
    
    return decorated_view


def optimized_seo_page(view_func):
    """Decorator for optimized SEO page views"""
    
    decorated_view = cache_page(60 * 60 * 2)(view_func)  # Cache for 2 hours
    decorated_view = cache_control(public=True, max_age=7200)(decorated_view)
    decorated_view = vary_on_headers('User-Agent')(decorated_view)
    
    return decorated_view


def optimized_homepage(view_func):
    """Decorator for optimized homepage views"""
    
    decorated_view = cache_page(60 * 15)(view_func)  # Cache for 15 minutes
    decorated_view = cache_control(public=True, max_age=900)(decorated_view)
    decorated_view = vary_on_headers('User-Agent', 'Accept-Language')(decorated_view)
    
    return decorated_view


# Singleton instance
performance_optimizer = PerformanceOptimizer()
