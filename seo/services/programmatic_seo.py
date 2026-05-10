"""
Programmatic SEO Page System
Generates scalable landing pages automatically for long-tail traffic
"""

from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, Count
from django.utils.text import slugify
from django.core.cache import cache
from seo.models import SEOCategory, SEOPage
from tools.models import Tool, ToolCategory
from tools.services.seo_content_generator import seo_content_generator
import random
import json


class ProgrammaticSEOEngine:
    """Advanced programmatic SEO page generation system"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 24  # 24 hours
        self.min_content_threshold = 300  # Minimum words for page quality
        self.max_variants_per_tool = 10
        
    def generate_programmatic_pages(self, tool: Tool) -> List[Dict[str, Any]]:
        """Generate programmatic SEO pages for a tool"""
        
        cache_key = f"prog_seo_pages_{tool.pk}"
        cached_pages = cache.get(cache_key)
        
        if cached_pages:
            return cached_pages
        
        pages = []
        
        # 1. Intent-based variations
        intent_pages = self._generate_intent_variations(tool)
        pages.extend(intent_pages)
        
        # 2. Use case variations
        use_case_pages = self._generate_use_case_variations(tool)
        pages.extend(use_case_pages)
        
        # 3. Audience variations
        audience_pages = self._generate_audience_variations(tool)
        pages.extend(audience_pages)
        
        # 4. Feature variations
        feature_pages = self._generate_feature_variations(tool)
        pages.extend(feature_pages)
        
        # 5. Comparison variations
        comparison_pages = self._generate_comparison_variations(tool)
        pages.extend(comparison_pages)
        
        # Filter and validate pages
        validated_pages = self._validate_pages(pages)
        
        cache.set(cache_key, validated_pages, self.cache_timeout)
        return validated_pages
    
    def _generate_intent_variations(self, tool: Tool) -> List[Dict[str, Any]]:
        """Generate intent-based page variations"""
        
        intents = {
            "online": {
                "keywords": ["online", "free", "web-based", "no download"],
                "templates": [
                    "Free Online {tool_name}",
                    "{tool_name} Online Free",
                    "Web-Based {tool_name}",
                    "No Download {tool_name}"
                ]
            },
            "use_case": {
                "keywords": ["for", "to", "purpose", "application"],
                "templates": [
                    "{tool_name} for {use_case}",
                    "Best {tool_name} for {use_case}",
                    "{tool_name} to {action}",
                    "Professional {tool_name} for {use_case}"
                ]
            },
            "without": {
                "keywords": ["without", "no", "skip", "bypass"],
                "templates": [
                    "{tool_name} Without {limitation}",
                    "Free {tool_name} No {limitation}",
                    "{tool_name} Without Registration",
                    "No Sign Up {tool_name}"
                ]
            },
            "vs": {
                "keywords": ["vs", "versus", "alternative", "comparison"],
                "templates": [
                    "{tool_name} vs {alternative}",
                    "Best {tool_name} Alternative",
                    "{tool_name} vs {competitor}",
                    "Free {tool_name} Alternative"
                ]
            },
            "how_to": {
                "keywords": ["how to", "tutorial", "guide", "step by step"],
                "templates": [
                    "How to Use {tool_name}",
                    "{tool_name} Tutorial",
                    "Step by Step {tool_name}",
                    "{tool_name} Guide"
                ]
            },
            "best": {
                "keywords": ["best", "top", "ultimate", "professional"],
                "templates": [
                    "Best {tool_name}",
                    "Top {tool_name} Online",
                    "Ultimate {tool_name}",
                    "Professional {tool_name}"
                ]
            }
        }
        
        pages = []
        
        for intent_type, intent_data in intents.items():
            # Generate 2-3 variations per intent
            for i in range(random.randint(2, 3)):
                template = random.choice(intent_data["templates"])
                
                if intent_type == "use_case":
                    use_case = self._get_random_use_case(tool)
                    if use_case:
                        title = template.format(tool_name=tool.name, use_case=use_case, action=self._get_action_verb(tool))
                    else:
                        continue
                elif intent_type == "without":
                    limitation = random.choice(["Registration", "Download", "Installation", "Payment", "Signup"])
                    title = template.format(tool_name=tool.name, limitation=limitation)
                elif intent_type == "vs":
                    alternative = self._get_alternative_tool(tool)
                    if alternative:
                        title = template.format(tool_name=tool.name, alternative=alternative, competitor=alternative)
                    else:
                        continue
                else:
                    title = template.format(tool_name=tool.name)
                
                page = self._create_page_variation(tool, title, intent_type, intent_data["keywords"])
                if page:
                    pages.append(page)
        
        return pages
    
    def _generate_use_case_variations(self, tool: Tool) -> List[Dict[str, Any]]:
        """Generate use case specific variations"""
        
        use_cases = tool.use_cases or self._generate_default_use_cases(tool)
        pages = []
        
        # Generate pages for top use cases
        for use_case in use_cases[:3]:
            title = f"{tool.name} for {use_case}"
            keywords = [use_case.lower(), tool.name.lower(), "free", "online"]
            
            page = self._create_page_variation(tool, title, "use_case", keywords)
            if page:
                pages.append(page)
        
        return pages
    
    def _generate_audience_variations(self, tool: Tool) -> List[Dict[str, Any]]:
        """Generate audience-specific variations"""
        
        audiences = self._get_target_audiences(tool)
        pages = []
        
        for audience in audiences[:2]:
            title = f"{tool.name} for {audience}"
            keywords = [audience.lower(), tool.name.lower(), "professional", "business"]
            
            page = self._create_page_variation(tool, title, "audience", keywords)
            if page:
                pages.append(page)
        
        return pages
    
    def _generate_feature_variations(self, tool: Tool) -> List[Dict[str, Any]]:
        """Generate feature-specific variations"""
        
        features = self._get_tool_features(tool)
        pages = []
        
        for feature in features[:2]:
            title = f"{feature} {tool.name}"
            keywords = [feature.lower(), tool.name.lower(), "advanced", "professional"]
            
            page = self._create_page_variation(tool, title, "feature", keywords)
            if page:
                pages.append(page)
        
        return pages
    
    def _generate_comparison_variations(self, tool: Tool) -> List[Dict[str, Any]]:
        """Generate comparison variations"""
        
        alternatives = self._get_competing_tools(tool)
        pages = []
        
        for alternative in alternatives[:2]:
            title = f"{tool.name} vs {alternative}"
            keywords = [tool.name.lower(), alternative.lower(), "vs", "comparison", "alternative"]
            
            page = self._create_page_variation(tool, title, "comparison", keywords)
            if page:
                pages.append(page)
        
        return pages
    
    def _create_page_variation(self, tool: Tool, title: str, variation_type: str, keywords: List[str]) -> Optional[Dict[str, Any]]:
        """Create a single page variation"""
        
        # Generate slug
        base_slug = slugify(title)
        slug = f"{tool.slug}-{base_slug}"
        
        # Check if slug is too long
        if len(slug) > 100:
            slug = slug[:100]
        
        # Generate unique content
        intro = self._generate_unique_intro(tool, title, variation_type, keywords)
        
        if len(intro.split()) < self.min_content_threshold:
            return None
        
        # Generate use cases for this variation
        use_cases = self._generate_variation_use_cases(tool, variation_type, keywords)
        
        # Generate FAQ for this variation
        faq_items = self._generate_variation_faq(tool, title, variation_type, keywords)
        
        # Generate examples
        examples = self._generate_variation_examples(tool, variation_type, keywords)
        
        # Create page data
        page_data = {
            "tool": tool,
            "title": title,
            "slug": slug,
            "variation_type": variation_type,
            "keywords": keywords,
            "intro": intro,
            "use_cases": use_cases,
            "faq_items": faq_items,
            "examples": examples,
            "meta_title": self._generate_meta_title(title, keywords),
            "meta_description": self._generate_meta_description(tool, title, keywords),
            "content_score": self._calculate_content_score(intro, use_cases, faq_items, examples)
        }
        
        return page_data
    
    def _generate_unique_intro(self, tool: Tool, title: str, variation_type: str, keywords: List[str]) -> str:
        """Generate unique introduction for the variation"""
        
        # Use the content generator with variation-specific context
        intro = seo_content_generator.generate_tool_intro(
            tool.name, 
            tool.short_desc, 
            tool.category.name,
            word_count=300
        )
        
        # Add variation-specific content
        variation_intro = self._get_variation_specific_intro(variation_type, title, keywords)
        
        return f"{intro}\n\n{variation_intro}"
    
    def _get_variation_specific_intro(self, variation_type: str, title: str, keywords: List[str]) -> str:
        """Get variation-specific introduction content"""
        
        if variation_type == "online":
            return f"Our {title} solution works entirely in your browser with no downloads required. Access powerful features instantly from any device."
        elif variation_type == "use_case":
            return f"Perfect for {keywords[0] if keywords else 'your specific needs'}, this specialized tool delivers professional results with unmatched ease of use."
        elif variation_type == "without":
            return f"Enjoy complete privacy and convenience with {title}. No registration, no software installation, no hidden costs."
        elif variation_type == "vs":
            return f"Discover why {title} stands out from the competition with superior features, faster processing, and better user experience."
        elif variation_type == "how_to":
            return f"Master {title} with our comprehensive guide. Learn professional techniques and best practices for optimal results."
        elif variation_type == "best":
            return f"Experience the best {title} available online. Professional-grade features, intuitive interface, and reliable results every time."
        elif variation_type == "audience":
            return f"Tailored specifically for {keywords[0] if keywords else 'professionals'}, this tool combines advanced features with user-friendly design."
        elif variation_type == "feature":
            return f"Leverage advanced {keywords[0] if keywords else 'features'} with our specialized tool. Built for professionals who demand excellence."
        elif variation_type == "comparison":
            return f"Compare {title} with alternatives and see why it's the preferred choice for professionals and businesses worldwide."
        else:
            return f"Discover the power and versatility of {title}. Designed for modern workflows and professional applications."
    
    def _generate_variation_use_cases(self, tool: Tool, variation_type: str, keywords: List[str]) -> List[str]:
        """Generate use cases specific to the variation"""
        
        base_use_cases = seo_content_generator.generate_use_cases(tool.name, tool.tags, count=5)
        
        # Filter and enhance based on variation type
        if variation_type == "use_case" and keywords:
            # Add use case specific to the keyword
            specific_use_case = f"Professional {keywords[0]} workflows and projects"
            if specific_use_case not in base_use_cases:
                base_use_cases.insert(0, specific_use_case)
        
        elif variation_type == "audience" and keywords:
            # Add audience-specific use case
            audience_use_case = f"Daily operations for {keywords[0]}"
            if audience_use_case not in base_use_cases:
                base_use_cases.insert(0, audience_use_case)
        
        return base_use_cases[:4]  # Return top 4 use cases
    
    def _generate_variation_faq(self, tool: Tool, title: str, variation_type: str, keywords: List[str]) -> List[Dict[str, str]]:
        """Generate FAQ items specific to the variation"""
        
        base_faq = seo_content_generator.generate_faq_items(tool.name, tool.short_desc, tool.category.name, count=5)
        
        # Add variation-specific FAQ
        variation_faq = self._get_variation_specific_faq(variation_type, title, keywords)
        
        if variation_faq:
            base_faq.insert(0, variation_faq)
        
        return base_faq[:5]  # Return top 5 FAQs
    
    def _get_variation_specific_faq(self, variation_type: str, title: str, keywords: List[str]) -> Dict[str, str]:
        """Get variation-specific FAQ item"""
        
        if variation_type == "online":
            return {
                "q": f"Is {title} really free and online?",
                "a": f"Yes, {title} is completely free to use with no registration required. It works entirely in your browser, so there's nothing to download or install."
            }
        elif variation_type == "use_case":
            return {
                "q": f"How does {title} help with {keywords[0] if keywords else 'specific tasks'}?",
                "a": f"Our tool is specifically optimized for {keywords[0] if keywords else 'your use case'} with features and workflows designed to deliver professional results efficiently."
            }
        elif variation_type == "without":
            return {
                "q": f"What do I need to use {title}?",
                "a": f"Absolutely nothing! No registration, no software installation, no payment. Just open the tool in your browser and start using it immediately."
            }
        elif variation_type == "vs":
            return {
                "q": f"How does {title} compare to alternatives?",
                "a": f"{title} offers superior performance, more features, better user experience, and completely free usage - unlike many alternatives that require payment or have limitations."
            }
        elif variation_type == "how_to":
            return {
                "q": f"Is {title} easy to use for beginners?",
                "a": f"Absolutely! Our tool is designed with an intuitive interface that makes it easy for beginners while still providing advanced features for professionals."
            }
        elif variation_type == "best":
            return {
                "q": f"What makes {title} the best choice?",
                "a": f"{title} combines professional-grade features, lightning-fast processing, intuitive design, and completely free usage - making it the best choice for all users."
            }
        
        return {}
    
    def _generate_variation_examples(self, tool: Tool, variation_type: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """Generate examples specific to the variation"""
        
        base_examples = seo_content_generator.generate_examples(tool.name, tool.short_desc, count=2)
        
        # Add variation-specific example
        if variation_type in ["use_case", "audience"] and keywords:
            specific_example = {
                "title": f"Example for {keywords[0]}",
                "description": f"Demonstrates how to use {tool.name} for {keywords[0]} scenarios",
                "input": self._get_contextual_input(tool, keywords[0]),
                "output": "Professional results optimized for your specific needs",
                "steps": ["Input your data", "Apply specialized settings", "Get tailored results"]
            }
            base_examples.insert(0, specific_example)
        
        return base_examples[:3]
    
    def _get_contextual_input(self, tool: Tool, context: str) -> str:
        """Get contextual example input based on use case/audience"""
        
        if "developer" in context.lower():
            return '{"name": "example", "type": "data", "format": "json"}'
        elif "student" in context.lower() or "education" in context.lower():
            return "Sample academic text for processing"
        elif "business" in context.lower():
            return "Professional business data example"
        else:
            return "Sample input for demonstration"
    
    def _generate_meta_title(self, title: str, keywords: List[str]) -> str:
        """Generate SEO-optimized meta title"""
        
        # Ensure title is under 70 characters
        if len(title) <= 70:
            return title
        
        # Truncate and add brand
        truncated = title[:65] + "..."
        return f"{truncated} | LamGen"
    
    def _generate_meta_description(self, tool: Tool, title: str, keywords: List[str]) -> str:
        """Generate SEO-optimized meta description"""
        
        base_desc = f"Free {title}. {tool.short_desc}"
        
        # Add keywords naturally
        if keywords:
            keyword_str = ", ".join(keywords[:3])
            base_desc += f" Perfect for {keyword_str}."
        
        # Ensure under 160 characters
        if len(base_desc) <= 160:
            return base_desc
        
        return base_desc[:157] + "..."
    
    def _calculate_content_score(self, intro: str, use_cases: List[str], faq_items: List[Dict], examples: List[Dict]) -> float:
        """Calculate content quality score"""
        
        score = 0.0
        
        # Word count contribution
        word_count = len(intro.split())
        if word_count >= 300:
            score += 0.3
        elif word_count >= 200:
            score += 0.2
        elif word_count >= 100:
            score += 0.1
        
        # Use cases contribution
        if len(use_cases) >= 4:
            score += 0.2
        elif len(use_cases) >= 2:
            score += 0.1
        
        # FAQ contribution
        if len(faq_items) >= 5:
            score += 0.2
        elif len(faq_items) >= 3:
            score += 0.1
        
        # Examples contribution
        if len(examples) >= 3:
            score += 0.2
        elif len(examples) >= 1:
            score += 0.1
        
        # Uniqueness bonus
        score += 0.1  # Assume good uniqueness for generated content
        
        return min(score, 1.0)
    
    def _validate_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and filter pages based on quality thresholds"""
        
        validated = []
        
        for page in pages:
            # Check content score
            if page.get("content_score", 0) < 0.5:
                continue
            
            # Check word count
            if len(page.get("intro", "").split()) < self.min_content_threshold:
                continue
            
            # Check for duplicate content
            if self._is_duplicate_content(page, validated):
                continue
            
            validated.append(page)
        
        return validated
    
    def _is_duplicate_content(self, page: Dict[str, Any], existing_pages: List[Dict[str, Any]]) -> bool:
        """Check if page content is too similar to existing pages"""
        
        page_text = f"{page.get('title', '')} {page.get('intro', '')}".lower()
        
        for existing in existing_pages:
            existing_text = f"{existing.get('title', '')} {existing.get('intro', '')}".lower()
            
            # Simple similarity check - could be enhanced with more sophisticated algorithms
            common_words = set(page_text.split()) & set(existing_text.split())
            similarity = len(common_words) / max(len(set(page_text.split())), len(set(existing_text.split())))
            
            if similarity > 0.7:  # 70% similarity threshold
                return True
        
        return False
    
    def _get_random_use_case(self, tool: Tool) -> Optional[str]:
        """Get a random use case for the tool"""
        
        use_cases = tool.use_cases or self._generate_default_use_cases(tool)
        return random.choice(use_cases) if use_cases else None
    
    def _generate_default_use_cases(self, tool: Tool) -> List[str]:
        """Generate default use cases for the tool"""
        
        return seo_content_generator.generate_use_cases(tool.name, tool.tags, count=8)
    
    def _get_action_verb(self, tool: Tool) -> str:
        """Get primary action verb for the tool"""
        
        return seo_content_generator._get_primary_verb(tool.name, tool.get_all_keywords())
    
    def _get_alternative_tool(self, tool: Tool) -> Optional[str]:
        """Get an alternative tool name for comparison"""
        
        alternatives = self._get_competing_tools(tool)
        return alternatives[0] if alternatives else None
    
    def _get_competing_tools(self, tool: Tool) -> List[str]:
        """Get competing tool names"""
        
        # Get tools from same category
        competing = Tool.objects.filter(
            category=tool.category,
            is_active=True
        ).exclude(id=tool.id).order_by('-view_count')[:5]
        
        return [comp.name for comp in competing]
    
    def _get_target_audiences(self, tool: Tool) -> List[str]:
        """Get target audiences for the tool"""
        
        audiences = ["Developers", "Designers", "Students", "Teachers", "Researchers", 
                    "Business Owners", "Marketers", "Content Creators", "Data Analysts"]
        
        # Filter based on tool keywords
        tool_keywords = tool.get_all_keywords()
        relevant_audiences = []
        
        for audience in audiences:
            audience_lower = audience.lower()
            if any(keyword in audience_lower for keyword in tool_keywords):
                relevant_audiences.append(audience)
        
        # If no specific matches, return general audiences
        if not relevant_audiences:
            relevant_audiences = ["Professionals", "Students", "Business Users"]
        
        return relevant_audiences
    
    def _get_tool_features(self, tool: Tool) -> List[str]:
        """Get key features of the tool"""
        
        features = ["Professional", "Advanced", "Fast", "Secure", "Free", "Online", 
                   "Easy to Use", "Accurate", "Reliable", "Instant"]
        
        # Filter based on tool characteristics
        relevant_features = []
        
        if tool.is_featured:
            relevant_features.append("Featured")
        
        if tool.view_count > 1000:
            relevant_features.append("Popular")
        
        if "fast" in tool.short_desc.lower() or "quick" in tool.short_desc.lower():
            relevant_features.append("Lightning Fast")
        
        if "secure" in tool.short_desc.lower() or "private" in tool.short_desc.lower():
            relevant_features.append("Secure")
        
        # Add some general features
        relevant_features.extend(random.sample(features, 3))
        
        return relevant_features[:5]
    
    def create_programmatic_pages_in_db(self, tool: Tool) -> int:
        """Create programmatic pages in database"""
        
        pages_data = self.generate_programmatic_pages(tool)
        created_count = 0
        
        for page_data in pages_data:
            # Check if page already exists
            existing_page = SEOPage.objects.filter(
                slug=page_data["slug"]
            ).first()
            
            if existing_page:
                continue
            
            # Find or create appropriate category
            category, created = SEOCategory.objects.get_or_create(
                slug="tool-variations",
                defaults={
                    "name": "Tool Variations",
                    "title_template": "{topic} — Tool Variation",
                    "meta_desc_template": "Specialized {topic} tool for specific use cases and needs."
                }
            )
            
            # Create SEO page
            seo_page = SEOPage.objects.create(
                category=category,
                topic=page_data["title"],
                slug=page_data["slug"],
                content_intro=page_data["intro"],
                items=page_data["use_cases"],
                meta_title=page_data["meta_title"],
                meta_description=page_data["meta_description"],
                is_active=True
            )
            
            created_count += 1
        
        return created_count
    
    def get_programmatic_seo_statistics(self) -> Dict[str, Any]:
        """Get statistics about programmatic SEO pages"""
        
        stats = {
            "total_seo_pages": SEOPage.objects.filter(is_active=True).count(),
            "total_categories": SEOCategory.objects.filter(is_active=True).count(),
            "pages_per_category": {},
            "most_viewed_pages": SEOPage.objects.filter(is_active=True).order_by('-view_count')[:10],
            "recent_pages": SEOPage.objects.filter(is_active=True).order_by('-created_at')[:10]
        }
        
        # Pages per category
        categories = SEOCategory.objects.filter(is_active=True).annotate(page_count=Count('pages'))
        stats["pages_per_category"] = {cat.name: cat.page_count for cat in categories}
        
        return stats


# Singleton instance
programmatic_seo_engine = ProgrammaticSEOEngine()
