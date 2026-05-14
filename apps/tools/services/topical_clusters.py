"""
Topical Cluster Architecture System
Builds category authority hubs for SEO dominance
"""

from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, Count, F, Avg
from django.core.cache import cache
from django.utils.text import slugify
from apps.tools.models import Tool, ToolCategory
from apps.seo.models import SEOPage
from apps.tools.services.seo_content_generator import seo_content_generator
from apps.tools.services.internal_linking import internal_linking_engine
import random
import json


class TopicalClusterEngine:
    """Advanced topical cluster system for category authority"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 12  # 12 hours
        self.min_tools_for_cluster = 3
        self.max_related_categories = 5
        
    def build_category_hub(self, category: ToolCategory) -> Dict[str, Any]:
        """Build comprehensive category hub page"""
        
        cache_key = f"category_hub_{category.pk}"
        cached_hub = cache.get(cache_key)
        
        if cached_hub:
            return cached_hub
        
        hub_data = {
            "category": category,
            "metadata": self._generate_category_metadata(category),
            "content_blocks": self._generate_category_content_blocks(category),
            "featured_tools": self._get_featured_tools(category),
            "tool_groups": self._group_tools_by_function(category),
            "trending_tools": category.get_trending_tools(6),
            "newest_tools": category.get_newest_tools(4),
            "related_categories": self._get_related_categories(category),
            "best_use_cases": self._get_category_use_cases(category),
            "related_guides": self._get_related_guides(category),
            "category_faq": self._generate_category_faq(category),
            "internal_links": self._get_category_internal_links(category),
            "seo_stats": self._get_category_seo_stats(category),
            "content_score": 0.0
        }
        
        # Calculate content score
        hub_data["content_score"] = self._calculate_hub_score(hub_data)
        
        cache.set(cache_key, hub_data, self.cache_timeout)
        return hub_data
    
    def _generate_category_metadata(self, category: ToolCategory) -> Dict[str, Any]:
        """Generate SEO metadata for category"""
        
        tool_count = category.active_tools_count
        
        # Generate title if not set
        if not category.seo_title:
            title = f"{category.name} — {tool_count} Free Online Tools | LamGen"
        else:
            title = category.seo_title
        
        # Generate description if not set
        if not category.seo_description:
            if category.description:
                desc = category.description[:157] + "..." if len(category.description) > 160 else category.description
            else:
                desc = f"Free {category.name.lower()} online. {tool_count} professional tools — no download, no signup, instant results. Perfect for developers, students, and professionals."
        else:
            desc = category.seo_description
        
        # Generate keyword variations
        keywords = self._generate_category_keywords(category)
        
        return {
            "title": title[:70],
            "description": desc[:160],
            "keywords": keywords,
            "tool_count": tool_count,
            "word_count_target": 1500,
            "content_depth": "comprehensive"
        }
    
    def _generate_category_keywords(self, category: ToolCategory) -> List[str]:
        """Generate keyword variations for category"""
        
        base_keywords = [
            category.name.lower(),
            f"free {category.name.lower()}",
            f"online {category.name.lower()}",
            f"{category.name.lower()} tools",
            f"professional {category.name.lower()}",
            f"{category.name.lower()} for developers",
            f"{category.name.lower()} for students",
            f"best {category.name.lower()}",
            f"{category.name.lower()} free"
        ]
        
        # Add tool-specific keywords
        tools = category.tools.filter(is_active=True)[:10]
        for tool in tools:
            tool_keywords = tool.get_all_keywords()
            base_keywords.extend([kw.lower() for kw in tool_keywords[:3]])
        
        # Remove duplicates and limit
        unique_keywords = list(set(base_keywords))[:20]
        return unique_keywords
    
    def _generate_category_content_blocks(self, category: ToolCategory) -> List[Dict[str, Any]]:
        """Generate content blocks for category page"""
        
        blocks = []
        
        # 1. Category introduction
        intro_block = {
            "type": "text",
            "title": f"About {category.name}",
            "subtitle": f"Professional {category.name.lower()} tools for modern workflows",
            "content": self._generate_category_intro(category)
        }
        blocks.append(intro_block)
        
        # 2. Key features
        features_block = {
            "type": "list",
            "title": "Key Features",
            "subtitle": "What makes our {category.name} tools exceptional",
            "items": self._generate_category_features(category)
        }
        blocks.append(features_block)
        
        # 3. Benefits
        benefits_block = {
            "type": "text",
            "title": "Why Choose Our {category.name} Tools",
            "content": self._generate_category_benefits(category)
        }
        blocks.append(benefits_block)
        
        # 4. Target audience
        audience_block = {
            "type": "list",
            "title": "Who Uses These Tools",
            "subtitle": "Perfect for professionals and enthusiasts",
            "items": self._generate_category_audience(category)
        }
        blocks.append(audience_block)
        
        # 5. Use cases
        use_cases_block = {
            "type": "steps",
            "title": "Common Use Cases",
            "subtitle": "How professionals use our {category.name} tools",
            "steps": self._generate_category_use_case_steps(category)
        }
        blocks.append(use_cases_block)
        
        return blocks
    
    def _generate_category_intro(self, category: ToolCategory) -> str:
        """Generate category introduction"""
        
        tool_count = category.active_tools_count
        
        if category.category_intro:
            return category.category_intro
        
        # Generate dynamic intro
        intro = f"Discover our comprehensive collection of {tool_count} professional {category.name.lower()} tools, designed to streamline your workflow and boost productivity. "
        
        intro += f"Whether you're a developer working on complex projects, a student learning new skills, or a professional managing daily tasks, "
        intro += f"our {category.name.lower()} tools provide the accuracy, speed, and reliability you need. "
        
        intro += f"Each tool is built with modern web technologies, ensuring fast performance and compatibility across all devices. "
        intro += f"No software installation required – access powerful {category.name.lower()} capabilities directly in your browser, "
        intro += f"with complete privacy and security for your data."
        
        return intro
    
    def _generate_category_features(self, category: ToolCategory) -> List[str]:
        """Generate category features list"""
        
        features = [
            f"Professional-grade {category.name.lower()} accuracy",
            "Lightning-fast processing and results",
            "Cross-platform compatibility (desktop, mobile, tablet)",
            "No registration or software installation required",
            "Secure local processing (data never leaves your device)",
            "Unlimited free usage with no restrictions",
            "Intuitive user-friendly interfaces",
            "Regular updates and feature improvements",
            "Advanced customization options",
            "Export and sharing capabilities"
        ]
        
        # Add category-specific features
        if "image" in category.name.lower():
            features.extend([
                "Multiple image format support",
                "High-quality output processing",
                "Batch processing capabilities"
            ])
        elif "text" in category.name.lower() or "writing" in category.name.lower():
            features.extend([
                "Real-time text analysis",
                "Multiple language support",
                "Professional formatting options"
            ])
        elif "data" in category.name.lower() or "json" in category.name.lower():
            features.extend([
                "Complex data structure handling",
                "Validation and error checking",
                "Schema support and validation"
            ])
        
        return features[:8]  # Return top 8 features
    
    def _generate_category_benefits(self, category: ToolCategory) -> str:
        """Generate category benefits content"""
        
        benefits = f"Our {category.name.lower()} tools offer significant advantages over traditional methods. "
        benefits += f"You'll save valuable time with instant processing, eliminate software installation and maintenance costs, "
        benefits += f"and enjoy the flexibility of working from any device with an internet connection. "
        
        benefits += f"Each tool is optimized for specific {category.name.lower()} tasks, ensuring professional-grade results "
        benefits += f"without the learning curve associated with complex software. "
        
        benefits += f"The browser-based approach means your data stays private and secure, "
        benefits += f"while regular updates ensure you always have access to the latest features and improvements. "
        
        benefits += f"Perfect for both individual professionals and teams, our tools scale to meet your needs "
        benefits += f"without requiring additional licenses or infrastructure."
        
        return benefits
    
    def _generate_category_audience(self, category: ToolCategory) -> List[str]:
        """Generate target audience list"""
        
        audiences = [
            "Software developers and programmers",
            "Students and educators",
            "Business professionals and analysts",
            "Content creators and marketers",
            "Designers and creative professionals",
            "Researchers and data scientists",
            "Freelancers and consultants",
            "Small business owners"
        ]
        
        # Filter based on category
        if "developer" in category.name.lower() or "code" in category.name.lower():
            audiences = [aud for aud in audiences if "developer" in aud.lower() or "programmer" in aud.lower()]
        elif "image" in category.name.lower() or "design" in category.name.lower():
            audiences = [aud for aud in audiences if "designer" in aud.lower() or "creative" in aud.lower()]
        elif "text" in category.name.lower() or "writing" in category.name.lower():
            audiences = [aud for aud in audiences if "content" in aud.lower() or "student" in aud.lower()]
        
        return audiences[:5]
    
    def _generate_category_use_case_steps(self, category: ToolCategory) -> List[Dict[str, str]]:
        """Generate use case steps"""
        
        steps = [
            {
                "title": "Step 1: Choose Your Tool",
                "content": f"Browse our {category.name.lower()} collection and select the tool that matches your specific needs."
            },
            {
                "title": "Step 2: Input Your Data",
                "content": "Provide your content, files, or parameters through our intuitive interface."
            },
            {
                "title": "Step 3: Process & Customize",
                "content": "Apply the tool's features and customize settings to achieve your desired results."
            },
            {
                "title": "Step 4: Review & Export",
                "content": "Review the processed results and export in your preferred format for immediate use."
            }
        ]
        
        return steps
    
    def _get_featured_tools(self, category: ToolCategory) -> List[Tool]:
        """Get featured tools for category"""
        
        return category.get_featured_tools_objects()
    
    def _group_tools_by_function(self, category: ToolCategory) -> List[Tuple[str, List[Tool]]]:
        """Group tools by function/purpose"""
        
        tools = list(category.tools.filter(is_active=True).order_by('order', 'name'))
        
        # Dynamic grouping based on tool names and tags
        tool_groups = {}
        
        for tool in tools:
            group_name = self._determine_tool_group(tool)
            if group_name not in tool_groups:
                tool_groups[group_name] = []
            tool_groups[group_name].append(tool)
        
        # Sort groups and convert to list
        sorted_groups = []
        for group_name in sorted(tool_groups.keys()):
            if group_name != "Other Tools":
                sorted_groups.append((group_name, tool_groups[group_name]))
        
        # Add "Other Tools" at the end if it exists
        if "Other Tools" in tool_groups:
            sorted_groups.append(("Other Tools", tool_groups["Other Tools"]))
        
        return sorted_groups
    
    def _determine_tool_group(self, tool: Tool) -> str:
        """Determine which group a tool belongs to"""
        
        name_lower = tool.name.lower()
        tags_lower = (tool.tags or "").lower()
        combined_text = f"{name_lower} {tags_lower}"
        
        # Grouping logic
        if any(word in combined_text for word in ["format", "beautify", "lint", "valid", "clean"]):
            return "Formatting & Validation"
        elif any(word in combined_text for word in ["convert", "transform", "change"]):
            return "Converters & Transformers"
        elif any(word in combined_text for word in ["generat", "create", "build", "make"]):
            return "Generators & Builders"
        elif any(word in combined_text for word in ["encod", "decod", "hash", "crypt", "secure"]):
            return "Security & Encoding"
        elif any(word in combined_text for word in ["compress", "minif", "optimiz", "reduce"]):
            return "Optimization Tools"
        elif any(word in combined_text for word in ["split", "merg", "join", "extract", "separate"]):
            return "Data Manipulation"
        elif any(word in combined_text for word in ["analyz", "check", "inspect", "test"]):
            return "Analysis & Testing"
        else:
            return "Other Tools"
    
    def _get_related_categories(self, category: ToolCategory) -> List[Dict[str, Any]]:
        """Get related categories for cross-linking"""
        
        all_categories = ToolCategory.objects.filter(is_active=True).exclude(id=category.id)
        
        # Simple related categories based on order proximity
        categories_list = list(all_categories.order_by('order', 'name'))
        
        # Find categories near in order
        current_index = None
        for i, cat in enumerate(categories_list):
            if cat.id == category.id:
                current_index = i
                break
        
        related = []
        if current_index is not None:
            start = max(0, current_index - 2)
            end = min(len(categories_list), current_index + 3)
            nearby_categories = categories_list[start:end]
        else:
            nearby_categories = categories_list[:self.max_related_categories]
        
        for cat in nearby_categories:
            related.append({
                "category": cat,
                "tool_count": cat.active_tools_count,
                "relevance_score": self._calculate_category_relevance(category, cat)
            })
        
        # Sort by relevance and return top results
        related.sort(key=lambda x: x["relevance_score"], reverse=True)
        return related[:self.max_related_categories]
    
    def _calculate_category_relevance(self, category1: ToolCategory, category2: ToolCategory) -> float:
        """Calculate relevance score between categories"""
        
        score = 0.0
        
        # Name similarity
        name1_words = set(category1.name.lower().split())
        name2_words = set(category2.name.lower().split())
        name_similarity = len(name1_words.intersection(name2_words)) / max(len(name1_words), len(name2_words))
        score += name_similarity * 0.3
        
        # Tool overlap (similar keywords)
        tools1 = category1.tools.filter(is_active=True)[:10]
        tools2 = category2.tools.filter(is_active=True)[:10]
        
        keywords1 = set()
        keywords2 = set()
        
        for tool in tools1:
            keywords1.update(tool.get_all_keywords())
        
        for tool in tools2:
            keywords2.update(tool.get_all_keywords())
        
        keyword_overlap = len(keywords1.intersection(keywords2)) / max(len(keywords1), len(keywords2))
        score += keyword_overlap * 0.4
        
        # Order proximity (closer in order = more related)
        order_diff = abs(category1.order - category2.order)
        order_score = max(0, 1 - (order_diff / 10))
        score += order_score * 0.3
        
        return score
    
    def _get_category_use_cases(self, category: ToolCategory) -> List[str]:
        """Get category-level use cases"""
        
        if category.best_use_cases:
            return category.best_use_cases
        
        # Generate from apps.tools
        all_use_cases = []
        tools = category.tools.filter(is_active=True)[:5]
        
        for tool in tools:
            tool_use_cases = tool.use_cases or seo_content_generator.generate_use_cases(tool.name, tool.tags, count=3)
            all_use_cases.extend(tool_use_cases[:2])
        
        # Remove duplicates and return
        unique_use_cases = list(set(all_use_cases))[:8]
        return unique_use_cases
    
    def _get_related_guides(self, category: ToolCategory) -> List[Dict[str, str]]:
        """Get related guides and tutorials"""
        
        if category.related_guides:
            return category.related_guides
        
        # Generate placeholder guides
        guides = [
            {
                "title": f"Complete Guide to {category.name}",
                "url": f"/guides/{category.slug}/",
                "description": f"Comprehensive tutorial for {category.name.lower()} tools"
            },
            {
                "title": f"{category.name} Best Practices",
                "url": f"/guides/{category.slug}-best-practices/",
                "description": f"Professional tips and techniques for {category.name.lower()}"
            },
            {
                "title": f"Advanced {category.name} Techniques",
                "url": f"/guides/advanced-{category.slug}/",
                "description": f"Take your {category.name.lower()} skills to the next level"
            }
        ]
        
        return guides
    
    def _generate_category_faq(self, category: ToolCategory) -> List[Dict[str, str]]:
        """Generate category-level FAQ"""
        
        if category.category_faq:
            return category.category_faq
        
        # Generate category-specific FAQ
        faq_items = [
            {
                "q": f"What are {category.name.lower()} tools?",
                "a": f"{category.name} tools are specialized software applications designed to help with specific {category.name.lower()} tasks. Our collection includes professional-grade tools that work entirely in your browser."
            },
            {
                "q": f"Are your {category.name.lower()} tools really free?",
                "a": f"Yes, all our {category.name.lower()} tools are completely free to use with no hidden charges, registration requirements, or usage limits."
            },
            {
                "q": f"Can I use these tools for commercial projects?",
                "a": f"Absolutely! Our {category.name.lower()} tools are perfect for both personal and commercial use. There are no restrictions on how you use the results."
            },
            {
                "q": f"Do I need to install any software?",
                "a": f"No installation required. All our {category.name.lower()} tools are web-based and work directly in your browser on any device."
            },
            {
                "q": f"How secure are my files and data?",
                "a": f"Your privacy is our priority. All processing happens locally in your browser, and your data never leaves your device or gets stored on our servers."
            }
        ]
        
        return faq_items
    
    def _get_category_internal_links(self, category: ToolCategory) -> List[Dict[str, Any]]:
        """Get internal links for category page"""
        
        return internal_linking_engine.get_category_internal_links(category)
    
    def _get_category_seo_stats(self, category: ToolCategory) -> Dict[str, Any]:
        """Get SEO statistics for category"""
        
        tools = category.tools.filter(is_active=True)
        
        stats = {
            "total_tools": tools.count(),
            "featured_tools": tools.filter(is_featured=True).count(),
            "new_tools": tools.filter(is_new=True).count(),
            "total_views": tools.aggregate(total=Count('view_count'))['total'] or 0,
            "avg_views_per_tool": tools.aggregate(avg=Avg('view_count'))['avg'] or 0,
            "tools_with_seo_content": tools.exclude(seo_intro='').count(),
            "content_completeness": 0.0
        }
        
        # Calculate content completeness
        if stats["total_tools"] > 0:
            completeness = (stats["tools_with_seo_content"] / stats["total_tools"]) * 100
            stats["content_completeness"] = round(completeness, 1)
        
        return stats
    
    def _calculate_hub_score(self, hub_data: Dict[str, Any]) -> float:
        """Calculate overall hub content score"""
        
        score = 0.0
        
        # Content blocks (30%)
        content_blocks = hub_data.get("content_blocks", [])
        if len(content_blocks) >= 5:
            score += 0.3
        elif len(content_blocks) >= 3:
            score += 0.2
        elif len(content_blocks) >= 1:
            score += 0.1
        
        # Tool count (20%)
        tool_count = hub_data.get("metadata", {}).get("tool_count", 0)
        if tool_count >= 10:
            score += 0.2
        elif tool_count >= 5:
            score += 0.15
        elif tool_count >= 3:
            score += 0.1
        
        # Featured tools (15%)
        featured_tools = hub_data.get("featured_tools", [])
        if len(featured_tools) >= 4:
            score += 0.15
        elif len(featured_tools) >= 2:
            score += 0.1
        
        # Related categories (10%)
        related_categories = hub_data.get("related_categories", [])
        if len(related_categories) >= 3:
            score += 0.1
        elif len(related_categories) >= 1:
            score += 0.05
        
        # FAQ items (10%)
        faq_items = hub_data.get("category_faq", [])
        if len(faq_items) >= 5:
            score += 0.1
        elif len(faq_items) >= 3:
            score += 0.05
        
        # Internal links (10%)
        internal_links = hub_data.get("internal_links", [])
        if len(internal_links) >= 8:
            score += 0.1
        elif len(internal_links) >= 5:
            score += 0.05
        
        # Use cases (5%)
        use_cases = hub_data.get("best_use_cases", [])
        if len(use_cases) >= 5:
            score += 0.05
        elif len(use_cases) >= 3:
            score += 0.025
        
        return min(score, 1.0)
    
    def generate_cross_category_clusters(self) -> Dict[str, Any]:
        """Generate cross-category topical clusters"""
        
        cache_key = "cross_category_clusters"
        cached_clusters = cache.get(cache_key)
        
        if cached_clusters:
            return cached_clusters
        
        clusters = {}
        
        # Get all active categories
        categories = ToolCategory.objects.filter(is_active=True).order_by('order', 'name')
        
        # Create clusters based on themes
        theme_clusters = {
            "Development Tools": [],
            "Content Creation": [],
            "Data Processing": [],
            "Utility Tools": [],
            "Media Processing": []
        }
        
        for category in categories:
            theme = self._categorize_theme(category)
            if theme in theme_clusters:
                theme_clusters[theme].append(category)
        
        # Build cluster data
        for theme, cats in theme_clusters.items():
            if len(cats) >= 2:  # Only include clusters with 2+ categories
                clusters[theme] = {
                    "categories": cats,
                    "total_tools": sum(cat.active_tools_count for cat in cats),
                    "featured_tools": self._get_cluster_featured_tools(cats),
                    "related_keywords": self._get_cluster_keywords(cats),
                    "cluster_score": self._calculate_cluster_score(cats)
                }
        
        cache.set(cache_key, clusters, self.cache_timeout)
        return clusters
    
    def _categorize_theme(self, category: ToolCategory) -> str:
        """Categorize a category into a theme"""
        
        name_lower = category.name.lower()
        
        if any(word in name_lower for word in ["developer", "code", "programming", "api"]):
            return "Development Tools"
        elif any(word in name_lower for word in ["text", "writing", "content", "markdown"]):
            return "Content Creation"
        elif any(word in name_lower for word in ["data", "json", "xml", "csv", "database"]):
            return "Data Processing"
        elif any(word in name_lower for word in ["image", "video", "media", "pdf"]):
            return "Media Processing"
        else:
            return "Utility Tools"
    
    def _get_cluster_featured_tools(self, categories: List[ToolCategory]) -> List[Tool]:
        """Get featured tools across cluster categories"""
        
        featured_tools = []
        for category in categories:
            tools = category.get_featured_tools_objects()
            featured_tools.extend(tools[:2])  # Top 2 per category
        
        # Sort by view count and return top 6
        featured_tools.sort(key=lambda t: t.view_count, reverse=True)
        return featured_tools[:6]
    
    def _get_cluster_keywords(self, categories: List[ToolCategory]) -> List[str]:
        """Get keywords for the entire cluster"""
        
        all_keywords = set()
        
        for category in categories:
            # Category keywords
            all_keywords.update([category.name.lower()])
            all_keywords.update([kw.lower() for kw in category.keyword_variations or []])
            
            # Tool keywords
            tools = category.tools.filter(is_active=True)[:5]
            for tool in tools:
                all_keywords.update(tool.get_all_keywords())
        
        return list(all_keywords)[:20]
    
    def _calculate_cluster_score(self, categories: List[ToolCategory]) -> float:
        """Calculate cluster authority score"""
        
        total_tools = sum(cat.active_tools_count for cat in categories)
        total_views = sum(cat.tools.filter(is_active=True).aggregate(total=Count('view_count'))['total'] or 0 for cat in categories)
        
        # Base score from tool count
        tool_score = min(total_tools / 20, 1.0) * 0.4
        
        # Score from views
        view_score = min(total_views / 10000, 1.0) * 0.3
        
        # Score from category count
        category_score = min(len(categories) / 5, 1.0) * 0.3
        
        return tool_score + view_score + category_score
    
    def get_topical_authority_report(self) -> Dict[str, Any]:
        """Generate comprehensive topical authority report"""
        
        report = {
            "total_categories": ToolCategory.objects.filter(is_active=True).count(),
            "total_tools": Tool.objects.filter(is_active=True).count(),
            "category_hubs": {},
            "cross_clusters": self.generate_cross_category_clusters(),
            "content_gaps": self._identify_content_gaps(),
            "optimization_opportunities": self._identify_optimization_opportunities(),
            "authority_scores": {}
        }
        
        # Analyze each category
        categories = ToolCategory.objects.filter(is_active=True)
        for category in categories:
            hub_data = self.build_category_hub(category)
            report["category_hubs"][category.slug] = {
                "name": category.name,
                "score": hub_data["content_score"],
                "tool_count": hub_data["metadata"]["tool_count"],
                "content_completeness": hub_data["seo_stats"]["content_completeness"]
            }
            
            # Calculate authority score
            authority_score = self._calculate_category_authority(category)
            report["authority_scores"][category.slug] = authority_score
        
        return report
    
    def _identify_content_gaps(self) -> List[Dict[str, Any]]:
        """Identify content gaps in topical clusters"""
        
        gaps = []
        
        categories = ToolCategory.objects.filter(is_active=True)
        
        for category in categories:
            hub_data = self.build_category_hub(category)
            
            # Check for missing content elements
            missing_elements = []
            
            if not hub_data.get("featured_tools"):
                missing_elements.append("featured_tools")
            
            if not hub_data.get("category_faq"):
                missing_elements.append("faq")
            
            if not hub_data.get("best_use_cases"):
                missing_elements.append("use_cases")
            
            if hub_data["seo_stats"]["content_completeness"] < 50:
                missing_elements.append("seo_content")
            
            if missing_elements:
                gaps.append({
                    "category": category.name,
                    "slug": category.slug,
                    "missing_elements": missing_elements,
                    "priority": "high" if len(missing_elements) >= 3 else "medium"
                })
        
        return gaps
    
    def _identify_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Identify optimization opportunities"""
        
        opportunities = []
        
        # Categories with low view counts
        low_view_categories = ToolCategory.objects.filter(
            is_active=True
        ).annotate(
            total_views=Count('tools__view_count')
        ).filter(total_views__lt=100)
        
        for category in low_view_categories:
            opportunities.append({
                "type": "low_traffic",
                "category": category.name,
                "slug": category.slug,
                "suggestion": "Improve SEO content and internal linking",
                "potential_impact": "medium"
            })
        
        # Tools without SEO content
        tools_without_seo = Tool.objects.filter(
            is_active=True,
            seo_intro=''
        ).select_related('category')
        
        for tool in tools_without_seo[:10]:  # Limit to top 10
            opportunities.append({
                "type": "missing_seo_content",
                "tool": tool.name,
                "category": tool.category.name,
                "suggestion": "Generate SEO content for tool page",
                "potential_impact": "high"
            })
        
        return opportunities
    
    def _calculate_category_authority(self, category: ToolCategory) -> float:
        """Calculate overall category authority score"""
        
        hub_data = self.build_category_hub(category)
        
        # Content score (40%)
        content_score = hub_data["content_score"] * 0.4
        
        # Tool diversity score (20%)
        tool_diversity = min(len(hub_data.get("tool_groups", [])) / 5, 1.0) * 0.2
        
        # Engagement score (20%)
        avg_views = hub_data["seo_stats"]["avg_views_per_tool"]
        engagement_score = min(avg_views / 1000, 1.0) * 0.2
        
        # Internal linking score (20%)
        internal_links = len(hub_data.get("internal_links", []))
        linking_score = min(internal_links / 10, 1.0) * 0.2
        
        return content_score + tool_diversity + engagement_score + linking_score


# Singleton instance
topical_cluster_engine = TopicalClusterEngine()
