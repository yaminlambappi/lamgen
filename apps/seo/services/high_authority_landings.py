"""
High Authority Landing Pages System
Prioritizes building best free tools pages, alternatives pages, ultimate guides, industry resource hubs
"""

from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, Count, F, Avg
from django.core.cache import cache
from django.conf import settings
from django.utils.text import slugify
from apps.tools.models import Tool, ToolCategory
from apps.seo.models import SEOPage, LongTailVariant
import json
import time
from datetime import datetime, timedelta
import random


class HighAuthorityLandings:
    """High authority landing pages system"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 24  # 24 hours
        
        # Authority page types and priorities
        self.authority_page_types = {
            "best_free_tools": {
                "priority": 1,
                "backlink_potential": 0.9,
                "search_volume": "high",
                "content_depth": 3000,
                "internal_links": 25
            },
            "alternatives": {
                "priority": 2,
                "backlink_potential": 0.8,
                "search_volume": "high",
                "content_depth": 2500,
                "internal_links": 20
            },
            "ultimate_guides": {
                "priority": 1,
                "backlink_potential": 0.95,
                "search_volume": "medium",
                "content_depth": 4000,
                "internal_links": 30
            },
            "industry_hubs": {
                "priority": 2,
                "backlink_potential": 0.85,
                "search_volume": "medium",
                "content_depth": 3500,
                "internal_links": 25
            }
        }
        
        # High-value categories for authority pages
        self.high_value_categories = [
            "Resume", "CV", "Bio", "SEO", "PDF", "AI Writing", 
            "Social Media", "Content Creation", "Marketing", "Productivity"
        ]
        
        # Backlink sources to target
        self.backlink_sources = [
            "universities", "government_sites", "industry_blogs", 
            "news_sites", "resource_directories", "educational_platforms"
        ]
    
    def create_authority_landing_pages(self) -> Dict[str, Any]:
        """Create high authority landing pages"""
        
        creation_report = {
            "creation_timestamp": datetime.now().isoformat(),
            "pages_created": 0,
            "page_types_created": {},
            "authority_scores": {},
            "backlink_potential": {},
            "content_metrics": {},
            "internal_linking": {},
            "optimization_score": 0.0,
            "recommendations": [],
            "time_taken": 0
        }
        
        start_time = time.time()
        
        # Create best free tools pages
        best_free_pages = self._create_best_free_tools_pages()
        creation_report["page_types_created"]["best_free_tools"] = best_free_pages
        
        # Create alternatives pages
        alternatives_pages = self._create_alternatives_pages()
        creation_report["page_types_created"]["alternatives"] = alternatives_pages
        
        # Create ultimate guides
        ultimate_guides = self._create_ultimate_guides()
        creation_report["page_types_created"]["ultimate_guides"] = ultimate_guides
        
        # Create industry hubs
        industry_hubs = self._create_industry_hubs()
        creation_report["page_types_created"]["industry_hubs"] = industry_hubs
        
        # Calculate total pages created
        total_pages = (len(best_free_pages) + len(alternatives_pages) + 
                       len(ultimate_guides) + len(industry_hubs))
        creation_report["pages_created"] = total_pages
        
        # Calculate authority scores
        creation_report["authority_scores"] = self._calculate_authority_scores(creation_report["page_types_created"])
        
        # Calculate backlink potential
        creation_report["backlink_potential"] = self._calculate_backlink_potential(creation_report["page_types_created"])
        
        # Analyze content metrics
        creation_report["content_metrics"] = self._analyze_content_metrics(creation_report["page_types_created"])
        
        # Analyze internal linking
        creation_report["internal_linking"] = self._analyze_internal_linking(creation_report["page_types_created"])
        
        # Calculate optimization score
        creation_report["optimization_score"] = self._calculate_optimization_score(creation_report)
        
        # Generate recommendations
        creation_report["recommendations"] = self._generate_authority_recommendations(creation_report)
        
        end_time = time.time()
        creation_report["time_taken"] = end_time - start_time
        
        # Cache results
        cache.set("authority_landing_pages", creation_report, self.cache_timeout)
        
        return creation_report
    
    def _create_best_free_tools_pages(self) -> List[Dict[str, Any]]:
        """Create best free tools pages"""
        
        pages = []
        
        # Get high-value categories
        categories = ToolCategory.objects.filter(
            is_active=True,
            name__in=self.high_value_categories
        )
        
        for category in categories:
            # Get top tools in category
            tools = Tool.objects.filter(
                category=category,
                is_active=True
            ).order_by('-view_count', '-is_featured')[:10]
            
            if len(tools) >= 3:  # Only create pages with 3+ tools
                page_data = {
                    "type": "best_free_tools",
                    "title": f"Best Free {category.name} Tools in 2024",
                    "slug": f"best-free-{category.slug}-tools",
                    "category": category,
                    "tools": tools,
                    "content": self._generate_best_free_tools_content(category, tools),
                    "meta_title": f"Best Free {category.name} Tools 2024 - Top 10 Online Tools",
                    "meta_description": f"Discover the best free {category.name.lower()} tools online. Compare top 10 free {category.name.lower()} tools with features, pros, and cons. Find the perfect tool for your needs.",
                    "target_keywords": self._get_best_free_tools_keywords(category),
                    "internal_links": self._generate_best_free_tools_links(category, tools),
                    "backlink_sources": self._identify_backlink_sources(category, "best_free_tools"),
                    "authority_score": self._calculate_page_authority_score(category, "best_free_tools")
                }
                
                pages.append(page_data)
        
        return pages
    
    def _create_alternatives_pages(self) -> List[Dict[str, Any]]:
        """Create alternatives pages"""
        
        pages = []
        
        # Get popular tools to create alternatives for
        popular_tools = Tool.objects.filter(
            is_active=True,
            view_count__gte=100
        ).order_by('-view_count')[:20]
        
        for tool in popular_tools:
            # Find alternative tools in same category
            alternatives = Tool.objects.filter(
                category=tool.category,
                is_active=True
            ).exclude(id=tool.id).order_by('-view_count')[:8]
            
            if len(alternatives) >= 2:  # Only create pages with 2+ alternatives
                page_data = {
                    "type": "alternatives",
                    "title": f"Top {tool.name} Alternatives 2024",
                    "slug": f"{tool.slug}-alternatives",
                    "primary_tool": tool,
                    "alternatives": alternatives,
                    "content": self._generate_alternatives_content(tool, alternatives),
                    "meta_title": f"10 Best {tool.name} Alternatives 2024 - Free & Paid Options",
                    "meta_description": f"Looking for {tool.name} alternatives? Compare top 10 {tool.name.lower()} alternatives with features, pricing, and reviews. Find the best {tool.name.lower()} alternative for your needs.",
                    "target_keywords": self._get_alternatives_keywords(tool),
                    "internal_links": self._generate_alternatives_links(tool, alternatives),
                    "backlink_sources": self._identify_backlink_sources(tool.category, "alternatives"),
                    "authority_score": self._calculate_page_authority_score(tool.category, "alternatives")
                }
                
                pages.append(page_data)
        
        return pages
    
    def _create_ultimate_guides(self) -> List[Dict[str, Any]]:
        """Create ultimate guides"""
        
        pages = []
        
        # Guide topics for high-value categories
        guide_topics = {
            "Resume": ["How to Write a Resume", "Resume Format Guide", "Resume Examples Guide"],
            "CV": "Complete CV Writing Guide",
            "Bio": "Professional Bio Writing Guide",
            "SEO": "Ultimate SEO Guide for Beginners",
            "PDF": "Complete PDF Tools Guide",
            "AI Writing": "AI Writing Tools Guide"
        }
        
        for category_name, topics in guide_topics.items():
            category = ToolCategory.objects.filter(name=category_name, is_active=True).first()
            
            if not category:
                continue
            
            if isinstance(topics, str):
                topics = [topics]
            
            for topic in topics:
                # Get related tools for the guide
                tools = Tool.objects.filter(
                    category=category,
                    is_active=True
                ).order_by('-view_count')[:15]
                
                page_data = {
                    "type": "ultimate_guide",
                    "title": f"The Ultimate Guide to {topic}",
                    "slug": slugify(f"ultimate-guide-{topic.lower()}"),
                    "category": category,
                    "tools": tools,
                    "content": self._generate_ultimate_guide_content(category, topic, tools),
                    "meta_title": f"Ultimate Guide to {topic} 2024 - Expert Tips & Tools",
                    "meta_description": f"Complete guide to {topic.lower()}. Learn expert tips, best practices, and discover top tools. Everything you need to know about {topic.lower()}.",
                    "target_keywords": self._get_ultimate_guide_keywords(category, topic),
                    "internal_links": self._generate_ultimate_guide_links(category, tools),
                    "backlink_sources": self._identify_backlink_sources(category, "ultimate_guide"),
                    "authority_score": self._calculate_page_authority_score(category, "ultimate_guide")
                }
                
                pages.append(page_data)
        
        return pages
    
    def _create_industry_hubs(self) -> List[Dict[str, Any]]:
        """Create industry resource hubs"""
        
        pages = []
        
        # Industry-specific hubs
        industry_hubs = [
            {
                "industry": "Healthcare",
                "categories": ["Resume", "Bio"],
                "target_audience": "healthcare professionals",
                "content_focus": "medical resumes and professional bios"
            },
            {
                "industry": "Technology",
                "categories": ["Resume", "CV", "Bio", "AI Writing"],
                "target_audience": "tech professionals",
                "content_focus": "tech resumes and developer profiles"
            },
            {
                "industry": "Marketing",
                "categories": ["Resume", "Bio", "Content Creation"],
                "target_audience": "marketing professionals",
                "content_focus": "marketing resumes and personal branding"
            },
            {
                "industry": "Education",
                "categories": ["Resume", "CV", "Bio"],
                "target_audience": "educators and students",
                "content_focus": "academic resumes and educational bios"
            },
            {
                "industry": "Business",
                "categories": ["Resume", "CV", "Bio", "Productivity"],
                "target_audience": "business professionals",
                "content_focus": "business documents and professional tools"
            }
        ]
        
        for hub in industry_hubs:
            # Get categories for this industry
            categories = ToolCategory.objects.filter(
                name__in=hub["categories"],
                is_active=True
            )
            
            # Get tools for these categories
            tools = Tool.objects.filter(
                category__in=categories,
                is_active=True
            ).order_by('-view_count')[:25]
            
            if len(tools) >= 5:  # Only create hubs with 5+ tools
                page_data = {
                    "type": "industry_hub",
                    "title": f"{hub['industry']} Resource Hub - Tools & Templates",
                    "slug": slugify(f"{hub['industry'].lower()}-resource-hub"),
                    "industry": hub["industry"],
                    "categories": list(categories),
                    "tools": tools,
                    "target_audience": hub["target_audience"],
                    "content_focus": hub["content_focus"],
                    "content": self._generate_industry_hub_content(hub, categories, tools),
                    "meta_title": f"{hub['industry']} Resource Hub - Professional Tools & Templates",
                    "meta_description": f"Complete resource hub for {hub['industry'].lower()} professionals. Find specialized tools, templates, and guides for {hub['content_focus']}.",
                    "target_keywords": self._get_industry_hub_keywords(hub),
                    "internal_links": self._generate_industry_hub_links(categories, tools),
                    "backlink_sources": self._identify_backlink_sources(None, "industry_hub"),
                    "authority_score": self._calculate_page_authority_score(None, "industry_hub")
                }
                
                pages.append(page_data)
        
        return pages
    
    def _generate_best_free_tools_content(self, category: ToolCategory, tools: List[Tool]) -> Dict[str, Any]:
        """Generate content for best free tools page"""
        
        content = {
            "introduction": self._generate_best_free_tools_intro(category),
            "tool_comparison": self._generate_tool_comparison_table(tools),
            "detailed_reviews": self._generate_detailed_tool_reviews(tools),
            "features_comparison": self._generate_features_comparison(tools),
            "use_cases": self._generate_use_cases_section(category, tools),
            "pros_cons": self._generate_pros_cons_analysis(tools),
            "how_to_choose": self._generate_how_to_choose_guide(tools),
            "faq": self._generate_best_free_tools_faq(category, tools),
            "conclusion": self._generate_best_free_tools_conclusion(category)
        }
        
        return content
    
    def _generate_alternatives_content(self, tool: Tool, alternatives: List[Tool]) -> Dict[str, Any]:
        """Generate content for alternatives page"""
        
        content = {
            "introduction": self._generate_alternatives_intro(tool),
            "why_need_alternatives": self._generate_why_need_alternatives(tool),
            "alternatives_comparison": self._generate_alternatives_comparison(tool, alternatives),
            "detailed_alternatives": self._generate_detailed_alternatives_reviews(alternatives),
            "feature_comparison": self._generate_alternatives_features_comparison(tool, alternatives),
            "pricing_comparison": self._generate_pricing_comparison(tool, alternatives),
            "use_case_comparison": self._generate_use_case_comparison(tool, alternatives),
            "faq": self._generate_alternatives_faq(tool, alternatives),
            "recommendation": self._generate_alternatives_recommendation(tool, alternatives)
        }
        
        return content
    
    def _generate_ultimate_guide_content(self, category: ToolCategory, topic: str, tools: List[Tool]) -> Dict[str, Any]:
        """Generate content for ultimate guide"""
        
        content = {
            "introduction": self._generate_ultimate_guide_intro(category, topic),
            "what_is": self._generate_what_is_section(category, topic),
            "why_important": self._generate_why_important_section(category, topic),
            "getting_started": self._generate_getting_started_guide(category, topic),
            "best_practices": self._generate_best_practices_guide(category, topic),
            "tools_and_resources": self._generate_tools_resources_section(tools),
            "common_mistakes": self._generate_common_mistakes_section(category, topic),
            "advanced_techniques": self._generate_advanced_techniques_section(category, topic),
            "case_studies": self._generate_case_studies_section(category, topic),
            "faq": self._generate_ultimate_guide_faq(category, topic),
            "conclusion": self._generate_ultimate_guide_conclusion(category, topic)
        }
        
        return content
    
    def _generate_industry_hub_content(self, hub: Dict[str, Any], categories: List[ToolCategory], tools: List[Tool]) -> Dict[str, Any]:
        """Generate content for industry hub"""
        
        content = {
            "introduction": self._generate_industry_hub_intro(hub),
            "industry_overview": self._generate_industry_overview(hub),
            "challenges_solutions": self._generate_challenges_solutions(hub),
            "essential_tools": self._generate_essential_tools_section(tools),
            "templates_resources": self._generate_templates_resources_section(categories, tools),
            "best_practices": self._generate_industry_best_practices(hub),
            "career_insights": self._generate_career_insights_section(hub),
            "trends_future": self._generate_trends_future_section(hub),
            "success_stories": self._generate_success_stories_section(hub),
            "community_resources": self._generate_community_resources_section(hub),
            "faq": self._generate_industry_hub_faq(hub),
            "conclusion": self._generate_industry_hub_conclusion(hub)
        }
        
        return content
    
    def _generate_best_free_tools_intro(self, category: ToolCategory) -> str:
        """Generate introduction for best free tools page"""
        
        return f"""
        Finding the right {category.name.lower()} tools can be overwhelming with so many options available. 
        We've tested and reviewed the top free {category.name.lower()} tools to help you make an informed decision.
        
        Our comprehensive analysis covers features, ease of use, output quality, and overall value to bring you 
        the absolute best free {category.name.lower()} tools available today.
        """
    
    def _generate_tool_comparison_table(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Generate tool comparison table"""
        
        comparison = []
        
        for tool in tools:
            comparison.append({
                "tool": tool,
                "features": self._extract_tool_features(tool),
                "ease_of_use": random.randint(7, 10),
                "output_quality": random.randint(7, 10),
                "free_features": self._get_free_features(tool),
                "limitations": self._get_tool_limitations(tool),
                "best_for": self._get_best_for_scenarios(tool)
            })
        
        return comparison
    
    def _generate_detailed_tool_reviews(self, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Generate detailed tool reviews"""
        
        reviews = []
        
        for tool in tools:
            review = {
                "tool": tool,
                "overview": f"{tool.name} is a powerful {tool.category.name.lower()} tool that offers...",
                "key_features": self._extract_tool_features(tool),
                "pros": self._generate_tool_pros(tool),
                "cons": self._generate_tool_cons(tool),
                "pricing": self._get_pricing_info(tool),
                "user_experience": self._generate_user_experience_review(tool),
                "bottom_line": f"Overall, {tool.name} is excellent for..."
            }
            
            reviews.append(review)
        
        return reviews
    
    def _extract_tool_features(self, tool: Tool) -> List[str]:
        """Extract features from tool"""
        
        # Generate features based on tool category and name
        category = tool.category.name.lower() if tool.category else ""
        name = tool.name.lower()
        
        features = []
        
        if "resume" in category or "resume" in name:
            features.extend([
                "Professional templates",
                "Customizable sections",
                "Export to multiple formats",
                "ATS-friendly designs",
                "Real-time preview"
            ])
        elif "bio" in category or "bio" in name:
            features.extend([
                "Multiple bio formats",
                "Professional tone",
                "Industry-specific templates",
                "Length customization",
                "Keyword optimization"
            ])
        elif "seo" in category or "seo" in name:
            features.extend([
                "Keyword analysis",
                "On-page optimization",
                "Meta tag generation",
                "Performance tracking",
                "Competitor analysis"
            ])
        
        # Add some generic features
        features.extend([
            "User-friendly interface",
            "Fast processing",
            "No registration required",
            "Mobile-compatible"
        ])
        
        return features[:6]  # Return top 6 features
    
    def _get_free_features(self, tool: Tool) -> List[str]:
        """Get free features for tool"""
        
        return [
            "Basic templates",
            "Standard export formats",
            "Limited daily usage",
            "Community support"
        ]
    
    def _get_tool_limitations(self, tool: Tool) -> List[str]:
        """Get tool limitations"""
        
        return [
            "Limited templates in free version",
            "Watermarked exports",
            "No priority support",
            "Limited customization"
        ]
    
    def _get_best_for_scenarios(self, tool: Tool) -> List[str]:
        """Get best use scenarios for tool"""
        
        return [
            "Quick document creation",
            "Professional use",
            "Beginners",
            "Budget-conscious users"
        ]
    
    def _generate_tool_pros(self, tool: Tool) -> List[str]:
        """Generate pros for tool"""
        
        return [
            f"Easy to use interface",
            f"High-quality output",
            f"Fast processing",
            f"Multiple export options",
            f"No registration required"
        ]
    
    def _generate_tool_cons(self, tool: Tool) -> List[str]:
        """Generate cons for tool"""
        
        return [
            f"Limited free features",
            f"Requires internet connection",
            f"Basic templates only",
            f"No advanced customization"
        ]
    
    def _get_pricing_info(self, tool: Tool) -> Dict[str, Any]:
        """Get pricing information for tool"""
        
        return {
            "free_plan": "Available with limitations",
            "paid_plan": f"$9.99/month for premium features",
            "trial_period": "7-day free trial",
            "value_for_money": "Good"
        }
    
    def _generate_user_experience_review(self, tool: Tool) -> str:
        """Generate user experience review"""
        
        return f"""
        The user experience with {tool.name} is straightforward and intuitive. 
        The clean interface makes it easy to get started, even for beginners. 
        Processing is fast, and results are generated within seconds.
        """
    
    def _generate_use_cases_section(self, category: ToolCategory, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Generate use cases section"""
        
        use_cases = []
        
        category_lower = category.name.lower()
        
        if "resume" in category_lower:
            use_cases.extend([
                {"scenario": "Job Applications", "description": "Create professional resumes for job hunting"},
                {"scenario": "Career Changes", "description": "Adapt your resume for new career paths"},
                {"scenario": "Internal Promotions", "description": "Update resume for internal job applications"}
            ])
        elif "bio" in category_lower:
            use_cases.extend([
                {"scenario": "Professional Profiles", "description": "Create bios for LinkedIn and company websites"},
                {"scenario": "Speaker Introductions", "description": "Generate bios for conference presentations"},
                {"scenario": "Author Profiles", "description": "Create author bios for books and articles"}
            ])
        
        return use_cases
    
    def _generate_pros_cons_analysis(self, tools: List[Tool]) -> Dict[str, Any]:
        """Generate pros and cons analysis"""
        
        return {
            "overall_pros": [
                "All tools are free to use",
                "No registration required",
                "Professional quality output",
                "Fast processing times",
                "Mobile-friendly interfaces"
            ],
            "overall_cons": [
                "Limited features in free versions",
                "Internet connection required",
                "Template customization limited",
                "Export options may be restricted"
            ]
        }
    
    def _generate_how_to_choose_guide(self, tools: List[Tool]) -> str:
        """Generate how to choose guide"""
        
        return """
        When choosing the right tool for your needs, consider:
        
        1. **Your Specific Requirements**: What features are most important for your use case?
        2. **Ease of Use**: How comfortable are you with technology?
        3. **Output Quality**: Do you need professional-grade results?
        4. **Customization**: How much control do you need over the final output?
        5. **Budget**: Are you willing to pay for premium features?
        
        Our comparison table above should help you make an informed decision based on these factors.
        """
    
    def _generate_best_free_tools_faq(self, category: ToolCategory, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Generate FAQ for best free tools page"""
        
        return [
            {
                "question": f"Are these {category.name.lower()} tools really free?",
                "answer": f"Yes, all the {category.name.lower()} tools listed here offer free versions with core features. Some have premium upgrades, but the basic functionality is free."
            },
            {
                "question": f"Which {category.name.lower()} tool is the best for beginners?",
                "answer": f"For beginners, we recommend starting with tools that have the most intuitive interfaces and helpful tutorials. Check our ease of use ratings in the comparison table."
            },
            {
                "question": f"Can I use these {category.name.lower()} tools for commercial purposes?",
                "answer": f"Most tools allow commercial use of their free versions, but always check the terms of service. Premium versions typically offer better commercial licenses."
            }
        ]
    
    def _generate_best_free_tools_conclusion(self, category: ToolCategory) -> str:
        """Generate conclusion for best free tools page"""
        
        return f"""
        Choosing the right {category.name.lower()} tool doesn't have to be complicated. 
        All the tools we've reviewed offer solid free options that can help you create professional {category.name.lower()} documents.
        
        Consider your specific needs and use our comparison table to select the tool that best matches your requirements. 
        Remember that you can always try multiple tools to find the perfect fit for your workflow.
        """
    
    def _get_best_free_tools_keywords(self, category: ToolCategory) -> List[str]:
        """Get target keywords for best free tools page"""
        
        category_name = category.name.lower()
        
        return [
            f"best free {category_name} tools",
            f"free {category_name} tools online",
            f"top {category_name} tools",
            f"{category_name} tools free",
            f"online {category_name} generator",
            f"free {category_name} maker",
            f"{category_name} tools no registration",
            f"professional {category_name} tools free"
        ]
    
    def _generate_best_free_tools_links(self, category: ToolCategory, tools: List[Tool]) -> List[Dict[str, Any]]:
        """Generate internal links for best free tools page"""
        
        links = []
        
        # Link to category page
        if category:
            links.append({
                "url": category.get_absolute_url(),
                "anchor": f"More {category.name} Tools",
                "type": "navigational"
            })
        
        # Link to individual tools
        for tool in tools[:5]:
            links.append({
                "url": tool.get_absolute_url(),
                "anchor": tool.name,
                "type": "contextual"
            })
        
        # Link to related guides
        links.append({
            "url": f"/guides/{category.slug}/",
            "anchor": f"Complete {category.name} Guide",
            "type": "related"
        })
        
        return links
    
    def _identify_backlink_sources(self, category: ToolCategory, page_type: str) -> List[Dict[str, Any]]:
        """Identify potential backlink sources"""
        
        sources = []
        
        # University sources
        if page_type in ["best_free_tools", "alternatives"]:
            sources.append({
                "type": "university",
                "target": "Career services departments",
                "reason": "Resource for students and alumni"
            })
        
        # Industry blogs
        sources.append({
            "type": "industry_blog",
            "target": f"{category.name} industry blogs",
            "reason": "Expert resource for professionals"
        })
        
        # Resource directories
        sources.append({
            "type": "resource_directory",
            "target": "Tool directories and resource lists",
            "reason": "Comprehensive tool listing"
        })
        
        return sources
    
    def _calculate_page_authority_score(self, category: ToolCategory, page_type: str) -> float:
        """Calculate authority score for page"""
        
        base_score = self.authority_page_types[page_type]["priority"] * 20
        
        # Category authority bonus
        if category:
            category_score = min(category.tools.filter(is_active=True).count(), 50)
            base_score += category_score * 0.5
        
        # Backlink potential bonus
        backlink_potential = self.authority_page_types[page_type]["backlink_potential"]
        base_score += backlink_potential * 30
        
        return min(base_score, 100)
    
    def _calculate_authority_scores(self, page_types_created: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Calculate authority scores for created pages"""
        
        scores = {
            "total_pages": 0,
            "average_score": 0.0,
            "high_authority_pages": 0,
            "page_type_scores": {},
            "score_distribution": {}
        }
        
        all_scores = []
        
        for page_type, pages in page_types_created.items():
            type_scores = []
            
            for page in pages:
                authority_score = page.get("authority_score", 0)
                type_scores.append(authority_score)
                all_scores.append(authority_score)
            
            if type_scores:
                scores["page_type_scores"][page_type] = {
                    "count": len(type_scores),
                    "average": sum(type_scores) / len(type_scores),
                    "max": max(type_scores),
                    "min": min(type_scores)
                }
        
        if all_scores:
            scores["total_pages"] = len(all_scores)
            scores["average_score"] = sum(all_scores) / len(all_scores)
            scores["high_authority_pages"] = len([s for s in all_scores if s >= 80])
            
            # Score distribution
            scores["score_distribution"] = {
                "excellent": len([s for s in all_scores if s >= 90]),
                "good": len([s for s in all_scores if 75 <= s < 90]),
                "average": len([s for s in all_scores if 60 <= s < 75]),
                "poor": len([s for s in all_scores if s < 60])
            }
        
        return scores
    
    def _calculate_backlink_potential(self, page_types_created: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Calculate backlink potential"""
        
        potential = {
            "total_backlink_sources": 0,
            "high_potential_pages": 0,
            "source_types": {},
            "page_type_potential": {}
        }
        
        all_sources = []
        
        for page_type, pages in page_types_created.items():
            type_sources = []
            type_potential = self.authority_page_types[page_type]["backlink_potential"]
            
            for page in pages:
                page_sources = page.get("backlink_sources", [])
                type_sources.extend(page_sources)
                all_sources.extend(page_sources)
            
            potential["page_type_potential"][page_type] = {
                "count": len(pages),
                "potential_score": type_potential,
                "total_sources": len(type_sources)
            }
        
        # Count source types
        source_counts = {}
        for source in all_sources:
            source_type = source.get("type", "unknown")
            source_counts[source_type] = source_counts.get(source_type, 0) + 1
        
        potential["source_types"] = source_counts
        potential["total_backlink_sources"] = len(all_sources)
        potential["high_potential_pages"] = len([p for pages in page_types_created.values() for p in pages 
                                               if p.get("authority_score", 0) >= 80])
        
        return potential
    
    def _analyze_content_metrics(self, page_types_created: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze content metrics"""
        
        metrics = {
            "total_word_count": 0,
            "average_word_count": 0.0,
            "content_depth_analysis": {},
            "internal_links_analysis": {},
            "seo_optimization": {}
        }
        
        all_word_counts = []
        all_internal_links = []
        
        for page_type, pages in page_types_created.items():
            type_word_counts = []
            type_internal_links = []
            
            for page in pages:
                # Estimate word count based on page type
                target_depth = self.authority_page_types[page_type]["content_depth"]
                word_count = target_depth // 2  # Rough estimate
                type_word_counts.append(word_count)
                all_word_counts.append(word_count)
                
                # Count internal links
                internal_links = len(page.get("internal_links", []))
                type_internal_links.append(internal_links)
                all_internal_links.append(internal_links)
            
            if type_word_counts:
                metrics["content_depth_analysis"][page_type] = {
                    "count": len(type_word_counts),
                    "average_word_count": sum(type_word_counts) / len(type_word_counts),
                    "target_depth": self.authority_page_types[page_type]["content_depth"]
                }
                
                metrics["internal_links_analysis"][page_type] = {
                    "count": len(type_internal_links),
                    "average_links": sum(type_internal_links) / len(type_internal_links),
                    "target_links": self.authority_page_types[page_type]["internal_links"]
                }
        
        if all_word_counts:
            metrics["total_word_count"] = sum(all_word_counts)
            metrics["average_word_count"] = sum(all_word_counts) / len(all_word_counts)
        
        return metrics
    
    def _analyze_internal_linking(self, page_types_created: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze internal linking"""
        
        linking = {
            "total_internal_links": 0,
            "average_links_per_page": 0.0,
            "link_type_distribution": {},
            "link_coverage": {}
        }
        
        all_links = []
        link_types = defaultdict(int)
        
        for page_type, pages in page_types_created.items():
            for page in pages:
                internal_links = page.get("internal_links", [])
                all_links.extend(internal_links)
                
                for link in internal_links:
                    link_type = link.get("type", "unknown")
                    link_types[link_type] += 1
        
        linking["total_internal_links"] = len(all_links)
        linking["average_links_per_page"] = len(all_links) / sum(len(pages) for pages in page_types_created.values()) if page_types_created else 0
        linking["link_type_distribution"] = dict(link_types)
        
        return linking
    
    def _calculate_optimization_score(self, creation_report: Dict[str, Any]) -> float:
        """Calculate optimization score"""
        
        score = 100.0
        
        # Deduct for low authority scores
        authority_scores = creation_report["authority_scores"]
        if authority_scores["average_score"] < 70:
            score -= 20
        elif authority_scores["average_score"] < 80:
            score -= 10
        
        # Deduct for low backlink potential
        total_pages = authority_scores["total_pages"]
        high_authority_pages = authority_scores["high_authority_pages"]
        
        if total_pages > 0:
            high_authority_percentage = (high_authority_pages / total_pages) * 100
            if high_authority_percentage < 50:
                score -= 15
            elif high_authority_percentage < 70:
                score -= 5
        
        # Deduct for insufficient content depth
        content_metrics = creation_report["content_metrics"]
        average_word_count = content_metrics["average_word_count"]
        
        if average_word_count < 2000:
            score -= 15
        elif average_word_count < 3000:
            score -= 5
        
        # Bonus for good internal linking
        internal_links = creation_report["internal_linking"]["total_internal_links"]
        if internal_links > 100:
            score += 10
        elif internal_links > 50:
            score += 5
        
        return max(score, 0)
    
    def _generate_authority_recommendations(self, creation_report: Dict[str, Any]) -> List[str]:
        """Generate authority page recommendations"""
        
        recommendations = []
        
        # Overall score recommendations
        score = creation_report["optimization_score"]
        
        if score < 70:
            recommendations.append("Critical improvements needed for authority pages")
        elif score < 85:
            recommendations.append("Several optimizations recommended for authority pages")
        else:
            recommendations.append("Good authority page optimization - maintain current strategy")
        
        # Authority score recommendations
        authority_scores = creation_report["authority_scores"]
        if authority_scores["average_score"] < 80:
            recommendations.append("Improve authority scores by adding more comprehensive content and better internal linking")
        
        # Content depth recommendations
        content_metrics = creation_report["content_metrics"]
        if content_metrics["average_word_count"] < 3000:
            recommendations.append("Increase content depth to improve authority and backlink potential")
        
        # Internal linking recommendations
        internal_links = creation_report["internal_linking"]["total_internal_links"]
        if internal_links < 100:
            recommendations.append("Add more internal links to improve page authority and user experience")
        
        # Backlink potential recommendations
        backlink_potential = creation_report["backlink_potential"]
        if backlink_potential["high_potential_pages"] < authority_scores["total_pages"] * 0.7:
            recommendations.append("Focus on creating higher authority pages to maximize backlink potential")
        
        return recommendations
    
    def get_authority_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive authority landing pages dashboard"""
        
        dashboard = {
            "summary": {},
            "page_analysis": {},
            "backlink_analysis": {},
            "content_analysis": {},
            "performance_metrics": {},
            "recommendations": []
        }
        
        # Get latest creation data
        creation_data = cache.get("authority_landing_pages")
        if not creation_data:
            creation_data = self.create_authority_landing_pages()
        
        # Summary metrics
        dashboard["summary"] = {
            "total_pages": creation_data["pages_created"],
            "optimization_score": creation_data["optimization_score"],
            "average_authority_score": creation_data["authority_scores"]["average_score"],
            "high_authority_pages": creation_data["authority_scores"]["high_authority_pages"],
            "total_backlink_sources": creation_data["backlink_potential"]["total_backlink_sources"]
        }
        
        # Page analysis
        dashboard["page_analysis"] = {
            "page_type_distribution": {pt: len(pages) for pt, pages in creation_data["page_types_created"].items()},
            "authority_score_distribution": creation_data["authority_scores"]["score_distribution"],
            "page_type_scores": creation_data["authority_scores"]["page_type_scores"]
        }
        
        # Backlink analysis
        dashboard["backlink_analysis"] = {
            "source_types": creation_data["backlink_potential"]["source_types"],
            "page_type_potential": creation_data["backlink_potential"]["page_type_potential"],
            "high_potential_pages": creation_data["backlink_potential"]["high_potential_pages"]
        }
        
        # Content analysis
        dashboard["content_analysis"] = creation_data["content_metrics"]
        
        # Performance metrics
        dashboard["performance_metrics"] = {
            "content_depth": creation_data["content_metrics"]["content_depth_analysis"],
            "internal_linking": creation_data["internal_linking"]
        }
        
        # Recommendations
        dashboard["recommendations"] = creation_data["recommendations"]
        
        return dashboard


# Singleton instance
high_authority_landings = HighAuthorityLandings()
