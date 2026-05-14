"""
Internal Linking Engine for SEO
Smart automatic internal linking to boost topical authority and user engagement
"""

from typing import List, Dict, Any, Optional, Set
from django.db.models import Q, F
from django.core.cache import cache
from apps.tools.models import Tool, ToolCategory
from apps.seo.models import SEOPage, LongTailVariant
import random
import math


class InternalLinkingEngine:
    """Advanced internal linking system for SEO optimization"""
    
    def __init__(self):
        self.cache_timeout = 60 * 30  # 30 minutes
        self.min_links_per_page = 8
        self.max_links_per_page = 20
        
    def get_tool_internal_links(self, tool: Tool, context_type: str = "tool_page") -> List[Dict[str, Any]]:
        """Generate internal links for a tool page"""
        
        cache_key = f"internal_links_tool_{tool.pk}_{context_type}"
        cached_links = cache.get(cache_key)
        
        if cached_links:
            return cached_links
        
        links = []
        
        # 1. Related tools by category (highest priority)
        category_links = self._get_category_related_tools(tool, limit=6)
        links.extend(category_links)
        
        # 2. Tools with keyword overlap
        keyword_links = self._get_keyword_related_tools(tool, exclude_ids=[l['tool_id'] for l in links], limit=4)
        links.extend(keyword_links)
        
        # 3. Trending tools in same category
        trending_links = self._get_trending_tools(tool.category, exclude_ids=[l['tool_id'] for l in links], limit=3)
        links.extend(trending_links)
        
        # 4. Featured tools from other categories
        featured_links = self._get_cross_category_featured(tool, exclude_ids=[l['tool_id'] for l in links], limit=2)
        links.extend(featured_links)
        
        # 5. SEO programmatic pages
        seo_links = self._get_related_seo_pages(tool, limit=3)
        links.extend(seo_links)
        
        # 6. Longtail variants
        longtail_links = self._get_longtail_variants(tool, limit=2)
        links.extend(longtail_links)
        
        # Ensure we meet minimum link requirements
        if len(links) < self.min_links_per_page:
            additional_links = self._get_fallback_links(tool, exclude_ids=[l['tool_id'] for l in links], 
                                                     target_count=self.min_links_per_page - len(links))
            links.extend(additional_links)
        
        # Limit to maximum links
        links = links[:self.max_links_per_page]
        
        # Add link metadata
        for link in links:
            link.update(self._get_link_metadata(link, tool))
        
        cache.set(cache_key, links, self.cache_timeout)
        return links
    
    def get_category_internal_links(self, category: ToolCategory) -> List[Dict[str, Any]]:
        """Generate internal links for a category page"""
        
        cache_key = f"internal_links_category_{category.pk}"
        cached_links = cache.get(cache_key)
        
        if cached_links:
            return cached_links
        
        links = []
        
        # 1. Featured tools in category
        featured_tools = category.get_featured_tools_objects()
        for tool in featured_tools[:4]:
            links.append(self._tool_to_link(tool, "featured_tool"))
        
        # 2. Trending tools in category
        trending_tools = category.get_trending_tools(limit=6)
        for tool in trending_tools:
            if tool.id not in [l['tool_id'] for l in links]:
                links.append(self._tool_to_link(tool, "trending_tool"))
        
        # 3. Newest tools in category
        newest_tools = category.get_newest_tools(limit=4)
        for tool in newest_tools:
            if tool.id not in [l['tool_id'] for l in links]:
                links.append(self._tool_to_link(tool, "new_tool"))
        
        # 4. Related categories
        related_categories = self._get_related_categories(category, limit=3)
        for rel_category in related_categories:
            links.append(self._category_to_link(rel_category, "related_category"))
        
        # 5. SEO pages for this category
        seo_pages = self._get_seo_pages_for_category(category, limit=3)
        for page in seo_pages:
            links.append(self._seo_page_to_link(page, "category_seo_page"))
        
        cache.set(cache_key, links, self.cache_timeout)
        return links
    
    def get_homepage_internal_links(self) -> List[Dict[str, Any]]:
        """Generate internal links for homepage"""
        
        cache_key = "internal_links_homepage"
        cached_links = cache.get(cache_key)
        
        if cached_links:
            return cached_links
        
        links = []
        
        # 1. Top categories
        top_categories = ToolCategory.objects.filter(is_active=True).order_by('order', 'name')[:6]
        for category in top_categories:
            links.append(self._category_to_link(category, "top_category"))
        
        # 2. Featured tools across all categories
        featured_tools = Tool.objects.filter(is_active=True, is_featured=True).select_related('category')[:8]
        for tool in featured_tools:
            links.append(self._tool_to_link(tool, "global_featured"))
        
        # 3. Trending tools globally
        trending_tools = Tool.objects.filter(is_active=True).order_by('-view_count').select_related('category')[:6]
        for tool in trending_tools:
            if tool.id not in [l['tool_id'] for l in links]:
                links.append(self._tool_to_link(tool, "global_trending"))
        
        # 4. Popular SEO pages
        popular_seo_pages = SEOPage.objects.filter(is_active=True).order_by('-view_count')[:4]
        for page in popular_seo_pages:
            links.append(self._seo_page_to_link(page, "popular_seo"))
        
        cache.set(cache_key, links, self.cache_timeout)
        return links
    
    def _get_category_related_tools(self, tool: Tool, limit: int = 6) -> List[Dict[str, Any]]:
        """Get related tools from the same category"""
        
        related_tools = Tool.objects.filter(
            category=tool.category,
            is_active=True
        ).exclude(id=tool.id).order_by('order', 'name')[:limit]
        
        links = []
        for related_tool in related_tools:
            links.append(self._tool_to_link(related_tool, "category_related"))
        
        return links
    
    def _get_keyword_related_tools(self, tool: Tool, exclude_ids: List[int] = None, limit: int = 4) -> List[Dict[str, Any]]:
        """Get tools with keyword overlap"""
        
        exclude_ids = exclude_ids or []
        tool_keywords = set(tool.get_all_keywords())
        
        if not tool_keywords:
            return []
        
        # Find tools with keyword overlap
        candidate_tools = Tool.objects.filter(
            is_active=True
        ).exclude(id=tool.id).exclude(id__in=exclude_ids)
        
        scored_tools = []
        for candidate in candidate_tools:
            candidate_keywords = set(candidate.get_all_keywords())
            overlap = len(tool_keywords.intersection(candidate_keywords))
            
            if overlap > 0:
                candidate.keyword_score = overlap
                scored_tools.append(candidate)
        
        # Sort by keyword overlap and view count
        scored_tools.sort(key=lambda t: (t.keyword_score, t.view_count), reverse=True)
        
        links = []
        for related_tool in scored_tools[:limit]:
            links.append(self._tool_to_link(related_tool, "keyword_related"))
        
        return links
    
    def _get_trending_tools(self, category: ToolCategory, exclude_ids: List[int] = None, limit: int = 3) -> List[Dict[str, Any]]:
        """Get trending tools in category"""
        
        exclude_ids = exclude_ids or []
        trending_tools = Tool.objects.filter(
            category=category,
            is_active=True
        ).exclude(id__in=exclude_ids).order_by('-view_count')[:limit]
        
        links = []
        for tool in trending_tools:
            links.append(self._tool_to_link(tool, "trending"))
        
        return links
    
    def _get_cross_category_featured(self, tool: Tool, exclude_ids: List[int] = None, limit: int = 2) -> List[Dict[str, Any]]:
        """Get featured tools from other categories"""
        
        exclude_ids = exclude_ids or []
        featured_tools = Tool.objects.filter(
            is_featured=True,
            is_active=True
        ).exclude(id=tool.id).exclude(id__in=exclude_ids).exclude(category=tool.category).select_related('category')[:limit]
        
        links = []
        for featured_tool in featured_tools:
            links.append(self._tool_to_link(featured_tool, "cross_category_featured"))
        
        return links
    
    def _get_related_seo_pages(self, tool: Tool, limit: int = 3) -> List[Dict[str, Any]]:
        """Get related SEO programmatic pages"""
        
        tool_keywords = tool.get_all_keywords()
        
        # Find SEO pages with matching keywords
        seo_pages = SEOPage.objects.filter(is_active=True)
        
        scored_pages = []
        for page in seo_pages:
            page_text = f"{page.topic} {' '.join(page.items)}".lower()
            score = 0
            
            for keyword in tool_keywords:
                if keyword.lower() in page_text:
                    score += 1
            
            if score > 0:
                page.seo_score = score
                scored_pages.append(page)
        
        scored_pages.sort(key=lambda p: p.seo_score, reverse=True)
        
        links = []
        for page in scored_pages[:limit]:
            links.append(self._seo_page_to_link(page, "keyword_related_seo"))
        
        return links
    
    def _get_longtail_variants(self, tool: Tool, limit: int = 2) -> List[Dict[str, Any]]:
        """Get longtail variants for the tool"""
        
        variants = LongTailVariant.objects.filter(
            tool=tool,
            is_active=True
        ).order_by('-view_count')[:limit]
        
        links = []
        for variant in variants:
            links.append(self._longtail_to_link(variant, "tool_variant"))
        
        return links
    
    def _get_fallback_links(self, tool: Tool, exclude_ids: List[int], target_count: int) -> List[Dict[str, Any]]:
        """Get fallback links to meet minimum requirements"""
        
        exclude_ids = exclude_ids or []
        
        # Get random tools from same category
        remaining_tools = Tool.objects.filter(
            category=tool.category,
            is_active=True
        ).exclude(id=tool.id).exclude(id__in=exclude_ids).order_by('?')[:target_count]
        
        links = []
        for fallback_tool in remaining_tools:
            links.append(self._tool_to_link(fallback_tool, "fallback"))
        
        return links
    
    def _get_related_categories(self, category: ToolCategory, limit: int = 3) -> List[ToolCategory]:
        """Get related categories based on keyword overlap or order proximity"""
        
        # Simple implementation: get categories with similar order
        all_categories = list(ToolCategory.objects.filter(is_active=True).exclude(id=category.id).order_by('order', 'name'))
        
        # Find categories near in order
        current_index = None
        for i, cat in enumerate(all_categories):
            if cat.id == category.id:
                current_index = i
                break
        
        if current_index is not None:
            # Get categories before and after
            start = max(0, current_index - 2)
            end = min(len(all_categories), current_index + 3)
            nearby_categories = all_categories[start:end]
        else:
            nearby_categories = all_categories[:limit]
        
        return nearby_categories[:limit]
    
    def _get_seo_pages_for_category(self, category: ToolCategory, limit: int = 3) -> List[SEOPage]:
        """Get SEO pages related to this category"""
        
        # This could be enhanced with category-SEO page relationships
        return SEOPage.objects.filter(is_active=True).order_by('-view_count')[:limit]
    
    def _tool_to_link(self, tool: Tool, link_type: str) -> Dict[str, Any]:
        """Convert tool to link format"""
        
        return {
            'type': 'tool',
            'tool_id': tool.id,
            'title': tool.name,
            'description': tool.short_desc,
            'url': tool.get_absolute_url(),
            'link_type': link_type,
            'category': tool.category.name,
            'category_slug': tool.category.slug,
            'icon': tool.icon,
            'is_featured': tool.is_featured,
            'is_new': tool.is_new,
            'view_count': tool.view_count,
            'color_from': tool.category.color_from,
            'color_to': tool.category.color_to
        }
    
    def _category_to_link(self, category: ToolCategory, link_type: str) -> Dict[str, Any]:
        """Convert category to link format"""
        
        return {
            'type': 'category',
            'category_id': category.id,
            'title': category.name,
            'description': category.short_desc or category.description[:100] + '...',
            'url': category.get_absolute_url(),
            'link_type': link_type,
            'slug': category.slug,
            'icon': category.icon,
            'tool_count': category.active_tools_count,
            'color_from': category.color_from,
            'color_to': category.color_to
        }
    
    def _seo_page_to_link(self, page: SEOPage, link_type: str) -> Dict[str, Any]:
        """Convert SEO page to link format"""
        
        return {
            'type': 'seo_page',
            'page_id': page.id,
            'title': page.topic,
            'description': page.meta_description or page.content_intro[:100] + '...',
            'url': page.get_absolute_url(),
            'link_type': link_type,
            'category': page.category.name,
            'category_slug': page.category.slug,
            'item_count': len(page.items),
            'view_count': page.view_count
        }
    
    def _longtail_to_link(self, variant: LongTailVariant, link_type: str) -> Dict[str, Any]:
        """Convert longtail variant to link format"""
        
        return {
            'type': 'longtail',
            'variant_id': variant.id,
            'title': variant.meta_title,
            'description': variant.meta_description,
            'url': variant.get_absolute_url(),
            'link_type': link_type,
            'tool_name': variant.tool.name,
            'tool_slug': variant.tool.slug,
            'category': variant.tool.category.name,
            'category_slug': variant.tool.category.slug,
            'keyword_intent': variant.keyword_intent
        }
    
    def _get_link_metadata(self, link: Dict[str, Any], context_tool: Tool) -> Dict[str, Any]:
        """Add metadata to link for SEO and display"""
        
        metadata = {
            'anchor_text_suggestions': self._generate_anchor_texts(link, context_tool),
            'relevance_score': self._calculate_relevance_score(link, context_tool),
            'priority': self._calculate_priority(link),
            'should_nofollow': self._should_nofollow(link),
            'link_attributes': self._get_link_attributes(link)
        }
        
        return metadata
    
    def _generate_anchor_texts(self, link: Dict[str, Any], context_tool: Tool) -> List[str]:
        """Generate anchor text suggestions"""
        
        base_title = link['title']
        suggestions = [base_title]
        
        # Add category-prefixed anchor
        if link['type'] == 'tool':
            suggestions.append(f"{link['category']} {base_title}")
        
        # Add benefit-oriented anchor
        if 'description' in link:
            desc_words = link['description'].split()[:3]
            suggestions.append(f"{' '.join(desc_words)} with {base_title}")
        
        # Add action-oriented anchor
        action_verbs = ['Try', 'Use', 'Explore', 'Discover']
        for verb in action_verbs:
            suggestions.append(f"{verb} {base_title}")
        
        return suggestions[:4]  # Return top 4 suggestions
    
    def _calculate_relevance_score(self, link: Dict[str, Any], context_tool: Tool) -> float:
        """Calculate relevance score (0.0 to 1.0)"""
        
        score = 0.0
        
        # Base relevance by type
        type_scores = {
            'category_related': 0.9,
            'keyword_related': 0.8,
            'trending': 0.7,
            'featured_tool': 0.6,
            'cross_category_featured': 0.5,
            'tool_variant': 0.8,
            'keyword_related_seo': 0.6
        }
        
        score = type_scores.get(link.get('link_type', ''), 0.5)
        
        # Boost for same category
        if link.get('category') == context_tool.category.name:
            score += 0.1
        
        # Boost for high view count
        if link.get('view_count', 0) > 1000:
            score += 0.1
        
        # Boost for featured/new status
        if link.get('is_featured') or link.get('is_new'):
            score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_priority(self, link: Dict[str, Any]) -> int:
        """Calculate display priority (1-10)"""
        
        priority = 5  # Base priority
        
        # Boost based on link type
        type_boosts = {
            'category_related': 3,
            'keyword_related': 2,
            'trending': 2,
            'featured_tool': 1,
            'tool_variant': 2
        }
        
        priority += type_boosts.get(link.get('link_type', ''), 0)
        
        # Boost for featured/new
        if link.get('is_featured'):
            priority += 1
        if link.get('is_new'):
            priority += 1
        
        return min(priority, 10)
    
    def _should_nofollow(self, link: Dict[str, Any]) -> bool:
        """Determine if link should be nofollow"""
        
        # Generally don't nofollow internal links
        return False
    
    def _get_link_attributes(self, link: Dict[str, Any]) -> Dict[str, str]:
        """Get HTML attributes for link"""
        
        attributes = {}
        
        # Add title attribute
        if 'description' in link:
            attributes['title'] = link['description'][:100]
        
        # Add data attributes for tracking
        attributes['data-link-type'] = link.get('link_type', '')
        attributes['data-link-id'] = str(link.get('tool_id', link.get('category_id', link.get('page_id', ''))))
        
        return attributes
    
    def invalidate_cache_for_tool(self, tool_id: int):
        """Invalidate cache when tool is updated"""
        
        # Clear various cache keys that might include this tool
        cache_patterns = [
            f"internal_links_tool_{tool_id}_",
            "internal_links_homepage",
            f"internal_links_category_"
        ]
        
        for pattern in cache_patterns:
            # This is a simplified cache invalidation
            # In production, you might want to use cache.delete_many with pattern matching
            cache.delete(pattern)
    
    def get_linking_statistics(self) -> Dict[str, Any]:
        """Get internal linking statistics for monitoring"""
        
        stats = {
            'total_tools': Tool.objects.filter(is_active=True).count(),
            'total_categories': ToolCategory.objects.filter(is_active=True).count(),
            'total_seo_pages': SEOPage.objects.filter(is_active=True).count(),
            'tools_with_seo_content': Tool.objects.filter(is_active=True).exclude(seo_intro='').count(),
            'categories_with_featured_tools': ToolCategory.objects.filter(is_active=True).exclude(featured_tools=[]).count(),
            'average_links_per_tool': 0,
            'link_coverage': 0
        }
        
        # Calculate average links per tool
        if stats['total_tools'] > 0:
            total_links = 0
            sample_tools = Tool.objects.filter(is_active=True)[:50]  # Sample for performance
            
            for tool in sample_tools:
                links = self.get_tool_internal_links(tool)
                total_links += len(links)
            
            stats['average_links_per_tool'] = total_links / len(sample_tools)
        
        return stats


# Singleton instance
internal_linking_engine = InternalLinkingEngine()
