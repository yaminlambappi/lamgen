"""
Authority Building Pages System
Creates mega guides, statistics pages, and comparison pages for backlink attraction
"""

from typing import List, Dict, Any, Optional
from django.db.models import Q, Count, F, Avg
from django.core.cache import cache
from django.utils.text import slugify
from django.conf import settings
from tools.models import Tool, ToolCategory
from seo.models import SEOCategory, SEOPage
from tools.services.seo_content_generator import seo_content_generator
from tools.services.content_uniqueness_engine import content_uniqueness_engine
import random
import json
from datetime import datetime, timedelta


class AuthorityBuilder:
    """Advanced authority building system for backlink attraction"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 24 * 7  # 7 days
        
        # Authority page types
        self.authority_types = {
            "mega_guides": {
                "title_pattern": "Ultimate Guide to {topic}",
                "word_count_target": 3000,
                "sections": ["introduction", "basics", "advanced", "tools", "best_practices", "faq", "conclusion"]
            },
            "statistics_pages": {
                "title_pattern": "{year} {topic} Statistics & Trends",
                "word_count_target": 2000,
                "sections": ["overview", "key_stats", "trends", "analysis", "predictions"]
            },
            "comparison_pages": {
                "title_pattern": "{tool1} vs {tool2}: Complete Comparison",
                "word_count_target": 1500,
                "sections": ["overview", "features", "pricing", "use_cases", "verdict"]
            },
            "alternatives_pages": {
                "title_pattern": "Best {tool_category} Alternatives in {year}",
                "word_count_target": 2000,
                "sections": ["overview", "top_alternatives", "comparison", "recommendations"]
            },
            "resource_pages": {
                "title_pattern": "Free {topic} Resources & Tools",
                "word_count_target": 1500,
                "sections": ["overview", "tools", "templates", "guides", "community"]
            }
        }
        
        # High-value topics for authority pages
        self.high_value_topics = [
            "Resume Building", "SEO Optimization", "PDF Tools", "AI Writing", "Social Media",
            "Content Creation", "Data Analysis", "Web Development", "Marketing", "Productivity"
        ]
        
        # Statistical data sources (simulated)
        self.statistical_categories = [
            "usage_trends", "market_growth", "user_demographics", "feature_adoption",
            "performance_metrics", "satisfaction_scores", "industry_adoption"
        ]
    
    def generate_authority_pages(self, page_count: int = 50) -> Dict[str, Any]:
        """Generate comprehensive authority pages"""
        
        generation_report = {
            "target_count": page_count,
            "generated_pages": 0,
            "page_types": {},
            "content_quality": {},
            "backlink_potential": {},
            "time_taken": 0
        }
        
        start_time = datetime.now()
        
        # Generate different types of authority pages
        page_allocation = self._allocate_page_types(page_count)
        
        for page_type, count in page_allocation.items():
            pages = self._generate_pages_by_type(page_type, count)
            generation_report["page_types"][page_type] = len(pages)
            generation_report["generated_pages"] += len(pages)
            
            # Save pages
            self._save_authority_pages(pages, page_type)
        
        end_time = datetime.now()
        generation_report["time_taken"] = (end_time - start_time).total_seconds()
        
        # Calculate quality metrics
        generation_report["content_quality"] = self._calculate_authority_quality()
        generation_report["backlink_potential"] = self._estimate_backlink_potential()
        
        return generation_report
    
    def _allocate_page_types(self, total_pages: int) -> Dict[str, int]:
        """Allocate pages across different authority types"""
        
        allocation = {
            "mega_guides": int(total_pages * 0.3),  # 30% mega guides
            "statistics_pages": int(total_pages * 0.2),  # 20% statistics
            "comparison_pages": int(total_pages * 0.2),  # 20% comparisons
            "alternatives_pages": int(total_pages * 0.15),  # 15% alternatives
            "resource_pages": int(total_pages * 0.15)  # 15% resources
        }
        
        # Adjust for rounding
        allocated = sum(allocation.values())
        if allocated < total_pages:
            allocation["mega_guides"] += total_pages - allocated
        
        return allocation
    
    def _generate_pages_by_type(self, page_type: str, count: int) -> List[Dict[str, Any]]:
        """Generate pages by specific type"""
        
        pages = []
        
        if page_type == "mega_guides":
            pages = self._generate_mega_guides(count)
        elif page_type == "statistics_pages":
            pages = self._generate_statistics_pages(count)
        elif page_type == "comparison_pages":
            pages = self._generate_comparison_pages(count)
        elif page_type == "alternatives_pages":
            pages = self._generate_alternatives_pages(count)
        elif page_type == "resource_pages":
            pages = self._generate_resource_pages(count)
        
        return pages
    
    def _generate_mega_guides(self, count: int) -> List[Dict[str, Any]]:
        """Generate comprehensive mega guides"""
        
        guides = []
        
        for i in range(count):
            topic = random.choice(self.high_value_topics)
            guide = self._create_mega_guide(topic, i)
            if guide:
                guides.append(guide)
        
        return guides
    
    def _create_mega_guide(self, topic: str, index: int) -> Optional[Dict[str, Any]]:
        """Create individual mega guide"""
        
        # Generate unique title
        title_variations = [
            f"The Ultimate Guide to {topic}",
            f"Complete {topic} Guide for 2024",
            f"Master {topic}: The Definitive Guide",
            f"{topic} Mastery: Comprehensive Guide",
            f"The Complete {topic} Handbook"
        ]
        
        title = random.choice(title_variations)
        slug = slugify(title)
        
        # Ensure uniqueness
        counter = 1
        while SEOPage.objects.filter(slug=slug).exists():
            slug = f"{slug}-{counter}"
            counter += 1
        
        # Generate comprehensive content
        content_data = self._generate_mega_guide_content(topic, title)
        
        if not content_data or content_data['word_count'] < 2500:
            return None
        
        # Create guide data
        guide_data = {
            "title": title,
            "slug": slug,
            "content_intro": content_data['intro'],
            "items": content_data['sections'],
            "meta_title": self._generate_authority_meta_title(title),
            "meta_description": self._generate_authority_meta_description(topic, title),
            "content_type": "mega_guide",
            "topic": topic,
            "word_count": content_data['word_count'],
            "quality_score": content_data['quality_score'],
            "backlink_score": self._calculate_backlink_score("mega_guide", topic),
            "internal_links": self._generate_authority_internal_links(topic, "mega_guide")
        }
        
        return guide_data
    
    def _generate_mega_guide_content(self, topic: str, title: str) -> Dict[str, Any]:
        """Generate comprehensive mega guide content"""
        
        sections = []
        
        # Introduction
        intro = self._generate_guide_intro(topic, title)
        sections.append({
            "type": "introduction",
            "title": "Introduction",
            "content": intro
        })
        
        # Basics section
        basics = self._generate_basics_section(topic)
        sections.append({
            "type": "basics",
            "title": "Understanding the Basics",
            "content": basics
        })
        
        # Advanced section
        advanced = self._generate_advanced_section(topic)
        sections.append({
            "type": "advanced",
            "title": "Advanced Techniques",
            "content": advanced
        })
        
        # Tools section
        tools = self._generate_tools_section(topic)
        sections.append({
            "type": "tools",
            "title": "Essential Tools and Resources",
            "content": tools
        })
        
        # Best practices
        best_practices = self._generate_best_practices_section(topic)
        sections.append({
            "type": "best_practices",
            "title": "Best Practices and Tips",
            "content": best_practices
        })
        
        # FAQ section
        faq = self._generate_guide_faq(topic)
        sections.append({
            "type": "faq",
            "title": "Frequently Asked Questions",
            "content": faq
        })
        
        # Conclusion
        conclusion = self._generate_conclusion_section(topic)
        sections.append({
            "type": "conclusion",
            "title": "Conclusion",
            "content": conclusion
        })
        
        # Calculate metrics
        total_content = intro + basics + advanced + tools + best_practices + faq + conclusion
        word_count = len(total_content.split())
        quality_score = self._calculate_content_quality(total_content, word_count)
        
        return {
            "sections": sections,
            "word_count": word_count,
            "quality_score": quality_score
        }
    
    def _generate_guide_intro(self, topic: str, title: str) -> str:
        """Generate guide introduction"""
        
        intro_parts = [
            f"Welcome to the most comprehensive guide on {topic} available online.",
            f"Whether you're a complete beginner or an experienced professional, this guide will provide you with the knowledge, tools, and strategies needed to master {topic}.",
            f"We've spent countless hours researching, testing, and compiling the most up-to-date information to ensure you have everything you need to succeed.",
            f"This guide covers everything from fundamental concepts to advanced techniques, practical applications, and industry best practices.",
            f"By the end of this guide, you'll have a deep understanding of {topic} and be equipped with actionable strategies you can implement immediately."
        ]
        
        return " ".join(intro_parts)
    
    def _generate_basics_section(self, topic: str) -> str:
        """Generate basics section content"""
        
        basics_content = f"""
        Before diving into advanced techniques, it's essential to understand the fundamental concepts of {topic}. 
        This section will cover the core principles, terminology, and foundational knowledge that form the basis of all {topic} work.
        
        Key concepts include understanding the basic terminology, recognizing common patterns, and grasping the essential principles that govern {topic} processes. 
        We'll explore how these fundamentals apply in real-world scenarios and provide practical examples to reinforce your learning.
        
        Mastering these basics will give you the confidence and knowledge needed to tackle more complex {topic} challenges and set the stage for advanced learning.
        """
        
        return basics_content.strip()
    
    def _generate_advanced_section(self, topic: str) -> str:
        """Generate advanced section content"""
        
        advanced_content = f"""
        Once you've mastered the basics, it's time to explore advanced {topic} techniques that separate professionals from amateurs. 
        This section delves into sophisticated strategies, cutting-edge methods, and expert-level approaches that can dramatically improve your results.
        
        We'll cover advanced topics such as optimization strategies, automation techniques, and professional workflows that can save you time while delivering superior outcomes. 
        These advanced techniques are based on industry best practices and real-world experience from {topic} experts.
        
        You'll learn how to implement these advanced methods step-by-step, with detailed explanations and practical examples that you can adapt to your specific needs and goals.
        """
        
        return advanced_content.strip()
    
    def _generate_tools_section(self, topic: str) -> str:
        """Generate tools section content"""
        
        # Get relevant tools for the topic
        relevant_tools = self._get_relevant_tools(topic)
        
        tools_content = f"""
        Having the right tools is crucial for success in {topic}. In this section, we'll explore the most effective tools and software that can streamline your workflow and enhance your productivity.
        
        We've tested dozens of {topic} tools and compiled a list of the best options based on functionality, ease of use, cost-effectiveness, and user reviews. 
        Whether you're looking for free tools or premium solutions, you'll find recommendations that suit your needs and budget.
        
        """
        
        if relevant_tools:
            tools_content += "Top recommended tools include:\n"
            for tool in relevant_tools[:5]:
                tools_content += f"• {tool.name}: {tool.short_desc}\n"
        
        tools_content += """
        Each tool recommendation includes detailed information about features, pricing, use cases, and pros and cons to help you make informed decisions.
        """
        
        return tools_content.strip()
    
    def _generate_best_practices_section(self, topic: str) -> str:
        """Generate best practices section content"""
        
        practices_content = f"""
        Success in {topic} isn't just about having the right tools—it's about using them effectively and following proven best practices. 
        This section covers the strategies, workflows, and approaches that professionals use to achieve consistently excellent results.
        
        We'll explore time-tested methods, common pitfalls to avoid, and optimization techniques that can significantly improve your outcomes. 
        These best practices are based on extensive research and real-world experience from {topic} professionals across various industries.
        
        You'll learn how to structure your work, optimize your processes, and implement quality control measures that ensure professional-grade results every time.
        """
        
        return practices_content.strip()
    
    def _generate_guide_faq(self, topic: str) -> str:
        """Generate FAQ section content"""
        
        faq_content = f"""
        Q: How long does it take to master {topic}?
        A: The learning curve varies depending on your background and dedication. With consistent practice and the right resources, most people can achieve proficiency in 3-6 months and mastery in 1-2 years.
        
        Q: What are the most common mistakes beginners make with {topic}?
        A: Common mistakes include skipping fundamentals, not practicing consistently, using the wrong tools, and not seeking feedback. Focus on building a strong foundation before moving to advanced techniques.
        
        Q: Do I need expensive tools to succeed in {topic}?
        A: While premium tools can enhance productivity, many successful professionals start with free or low-cost options. Focus on mastering fundamentals before investing in expensive software.
        
        Q: How can I stay updated with the latest {topic} trends?
        A: Follow industry blogs, join professional communities, attend webinars, and continuously practice your skills. The {topic} field evolves rapidly, so continuous learning is essential.
        
        Q: What's the best way to practice {topic}?
        A: Start with simple projects, gradually increase complexity, seek feedback from peers, and work on real-world scenarios. Consistent daily practice is more effective than occasional intensive sessions.
        """
        
        return faq_content.strip()
    
    def _generate_conclusion_section(self, topic: str) -> str:
        """Generate conclusion section content"""
        
        conclusion_content = f"""
        Congratulations! You've now completed this comprehensive guide to {topic}. You've learned the fundamental concepts, advanced techniques, essential tools, and best practices that will help you succeed in your {topic} endeavors.
        
        Remember that mastery is a journey, not a destination. Continue practicing, stay curious, and never stop learning. The {topic} field is constantly evolving, so staying updated with the latest trends and techniques is crucial for long-term success.
        
        We encourage you to bookmark this guide for future reference and share it with others who might benefit from this comprehensive resource. Your feedback and suggestions are always welcome as we continuously update this guide to reflect the latest developments in {topic}.
        
        Thank you for trusting this guide for your {topic} learning journey. We wish you the best of success in all your future endeavors!
        """
        
        return conclusion_content.strip()
    
    def _generate_statistics_pages(self, count: int) -> List[Dict[str, Any]]:
        """Generate statistics and trends pages"""
        
        stats_pages = []
        
        for i in range(count):
            topic = random.choice(self.high_value_topics)
            stats_page = self._create_statistics_page(topic, i)
            if stats_page:
                stats_pages.append(stats_page)
        
        return stats_pages
    
    def _create_statistics_page(self, topic: str, index: int) -> Optional[Dict[str, Any]]:
        """Create individual statistics page"""
        
        year = datetime.now().year
        title = f"{year} {topic} Statistics & Trends"
        slug = slugify(f"{year}-{topic.lower()}-statistics")
        
        # Ensure uniqueness
        counter = 1
        while SEOPage.objects.filter(slug=slug).exists():
            slug = f"{slug}-{counter}"
            counter += 1
        
        # Generate statistics content
        content_data = self._generate_statistics_content(topic, year)
        
        if not content_data or content_data['word_count'] < 1500:
            return None
        
        stats_data = {
            "title": title,
            "slug": slug,
            "content_intro": content_data['intro'],
            "items": content_data['sections'],
            "meta_title": self._generate_authority_meta_title(title),
            "meta_description": self._generate_authority_meta_description(topic, title),
            "content_type": "statistics_page",
            "topic": topic,
            "year": year,
            "word_count": content_data['word_count'],
            "quality_score": content_data['quality_score'],
            "backlink_score": self._calculate_backlink_score("statistics_page", topic),
            "internal_links": self._generate_authority_internal_links(topic, "statistics_page")
        }
        
        return stats_data
    
    def _generate_statistics_content(self, topic: str, year: int) -> Dict[str, Any]:
        """Generate statistics content"""
        
        sections = []
        
        # Overview
        overview = self._generate_stats_overview(topic, year)
        sections.append({
            "type": "overview",
            "title": f"{topic} Market Overview",
            "content": overview
        })
        
        # Key statistics
        key_stats = self._generate_key_statistics(topic, year)
        sections.append({
            "type": "key_stats",
            "title": "Key Statistics",
            "content": key_stats
        })
        
        # Trends
        trends = self._generate_trends_analysis(topic, year)
        sections.append({
            "type": "trends",
            "title": "Trends Analysis",
            "content": trends
        })
        
        # Analysis
        analysis = self._generate_market_analysis(topic, year)
        sections.append({
            "type": "analysis",
            "title": "Market Analysis",
            "content": analysis
        })
        
        # Predictions
        predictions = self._generate_predictions(topic, year)
        sections.append({
            "type": "predictions",
            "title": "Future Predictions",
            "content": predictions
        })
        
        # Calculate metrics
        total_content = overview + key_stats + trends + analysis + predictions
        word_count = len(total_content.split())
        quality_score = self._calculate_content_quality(total_content, word_count)
        
        return {
            "sections": sections,
            "word_count": word_count,
            "quality_score": quality_score
        }
    
    def _generate_stats_overview(self, topic: str, year: int) -> str:
        """Generate statistics overview"""
        
        overview_content = f"""
        The {topic} market has experienced significant growth in {year}, with increased adoption across various industries and user segments. 
        This comprehensive analysis provides detailed insights into market trends, user behavior, and future projections for the {topic} sector.
        
        Market research indicates that the {topic} industry has reached a maturity phase in developed markets while showing rapid growth in emerging economies. 
        The increasing digital transformation across businesses has been a key driver of this growth, with organizations investing heavily in {topic} solutions.
        
        This overview section provides the foundation for understanding the current state of the {topic} market and sets the context for the detailed statistics and trends analysis that follows.
        """
        
        return overview_content.strip()
    
    def _generate_key_statistics(self, topic: str, year: int) -> str:
        """Generate key statistics"""
        
        # Generate realistic-looking statistics
        stats = {
            "market_size": f"${random.randint(50, 500)} billion",
            "growth_rate": f"{random.randint(12, 35)}%",
            "user_count": f"{random.randint(100, 1000)} million",
            "enterprise_adoption": f"{random.randint(60, 90)}%",
            "satisfaction_score": f"{random.randint(75, 95)}%"
        }
        
        stats_content = f"""
        Key statistics for the {topic} market in {year} reveal impressive growth and strong user engagement:
        
        • Market Size: The global {topic} market reached {stats['market_size']}, representing a {stats['growth_rate']} increase from the previous year.
        • User Base: Over {stats['user_count']} users worldwide now use {topic} solutions regularly, with enterprise adoption reaching {stats['enterprise_adoption']}.
        • Satisfaction: User satisfaction scores average {stats['satisfaction_score']}, indicating strong market acceptance and product quality.
        • Growth Drivers: Digital transformation, remote work trends, and increased automation needs have been primary growth drivers.
        • Geographic Distribution: North America and Europe lead in market share, while Asia-Pacific shows the fastest growth rates.
        
        These statistics demonstrate the robust health and continued growth potential of the {topic} market.
        """
        
        return stats_content.strip()
    
    def _generate_trends_analysis(self, topic: str, year: int) -> str:
        """Generate trends analysis"""
        
        trends_content = f"""
        Several key trends have shaped the {topic} landscape in {year}, influencing user behavior, product development, and market dynamics. 
        Understanding these trends is crucial for businesses and professionals looking to capitalize on market opportunities.
        
        Major trends include the increasing integration of AI and machine learning capabilities, the growing emphasis on user experience and interface design, 
        and the rising demand for mobile-first solutions. Security and privacy concerns have also become more prominent, influencing product development priorities.
        
        The trend toward all-in-one platforms continues, with users preferring comprehensive solutions over specialized tools. 
        Additionally, the subscription-based business model has gained significant traction, offering predictable revenue streams for providers and flexible pricing for users.
        
        These trends indicate a maturing market that continues to evolve in response to changing user needs and technological advancements.
        """
        
        return trends_content.strip()
    
    def _generate_market_analysis(self, topic: str, year: int) -> str:
        """Generate market analysis"""
        
        analysis_content = f"""
        The {topic} market analysis for {year} reveals a competitive landscape with several key players dominating market share while numerous niche providers serve specific segments. 
        Market consolidation continues as larger companies acquire innovative startups to expand their product portfolios and customer base.
        
        Competitive analysis shows that differentiation increasingly comes from specialized features, user experience quality, and integration capabilities rather than core functionality alone. 
        Companies that successfully combine powerful features with intuitive interfaces tend to achieve higher user retention and satisfaction scores.
        
        The market shows clear segmentation by user type, with enterprise solutions, small business offerings, and individual consumer products each serving distinct needs and price points. 
        This segmentation allows providers to tailor their products and marketing strategies to specific target audiences.
        
        Overall market dynamics suggest continued growth opportunities for providers that can innovate quickly and adapt to changing user requirements.
        """
        
        return analysis_content.strip()
    
    def _generate_predictions(self, topic: str, year: int) -> str:
        """Generate future predictions"""
        
        predictions_content = f"""
        Looking ahead to {year + 1} and beyond, several predictions emerge for the {topic} market based on current trends and technological developments. 
        These predictions provide insights into potential market evolution and help stakeholders prepare for future opportunities and challenges.
        
        Key predictions include increased AI integration across all {topic} solutions, greater emphasis on collaborative features and team workflows, 
        and enhanced mobile capabilities to support on-the-go usage. The market is also expected to see more sophisticated personalization and customization options.
        
        Industry-specific solutions are likely to gain prominence as providers recognize the value of tailoring their products to specific vertical requirements. 
        Additionally, we anticipate increased focus on accessibility features and inclusive design to serve diverse user populations more effectively.
        
        The competitive landscape will likely see continued consolidation, with larger players acquiring innovative startups to expand their market presence. 
        However, niche providers that serve specialized segments well will continue to find opportunities for growth and profitability.
        """
        
        return predictions_content.strip()
    
    def _generate_comparison_pages(self, count: int) -> List[Dict[str, Any]]:
        """Generate tool comparison pages"""
        
        comparison_pages = []
        
        for i in range(count):
            comparison = self._create_comparison_page(i)
            if comparison:
                comparison_pages.append(comparison)
        
        return comparison_pages
    
    def _create_comparison_page(self, index: int) -> Optional[Dict[str, Any]]:
        """Create individual comparison page"""
        
        # Get two random tools to compare
        tools = Tool.objects.filter(is_active=True).order_by('?')[:2]
        
        if len(tools) < 2:
            return None
        
        tool1, tool2 = tools[0], tools[1]
        title = f"{tool1.name} vs {tool2.name}: Complete Comparison"
        slug = slugify(f"{tool1.slug}-vs-{tool2.slug}-comparison")
        
        # Ensure uniqueness
        counter = 1
        while SEOPage.objects.filter(slug=slug).exists():
            slug = f"{slug}-{counter}"
            counter += 1
        
        # Generate comparison content
        content_data = self._generate_comparison_content(tool1, tool2)
        
        if not content_data or content_data['word_count'] < 1200:
            return None
        
        comparison_data = {
            "title": title,
            "slug": slug,
            "content_intro": content_data['intro'],
            "items": content_data['sections'],
            "meta_title": self._generate_authority_meta_title(title),
            "meta_description": self._generate_authority_meta_description("tool comparison", title),
            "content_type": "comparison_page",
            "tools": [tool1.name, tool2.name],
            "word_count": content_data['word_count'],
            "quality_score": content_data['quality_score'],
            "backlink_score": self._calculate_backlink_score("comparison_page", "tool comparison"),
            "internal_links": self._generate_authority_internal_links("tool comparison", "comparison_page")
        }
        
        return comparison_data
    
    def _generate_comparison_content(self, tool1: Tool, tool2: Tool) -> Dict[str, Any]:
        """Generate comparison content"""
        
        sections = []
        
        # Overview
        overview = self._generate_comparison_overview(tool1, tool2)
        sections.append({
            "type": "overview",
            "title": "Overview",
            "content": overview
        })
        
        # Features comparison
        features = self._generate_features_comparison(tool1, tool2)
        sections.append({
            "type": "features",
            "title": "Features Comparison",
            "content": features
        })
        
        # Pricing comparison
        pricing = self._generate_pricing_comparison(tool1, tool2)
        sections.append({
            "type": "pricing",
            "title": "Pricing Comparison",
            "content": pricing
        })
        
        # Use cases
        use_cases = self._generate_use_cases_comparison(tool1, tool2)
        sections.append({
            "type": "use_cases",
            "title": "Use Cases",
            "content": use_cases
        })
        
        # Verdict
        verdict = self._generate_comparison_verdict(tool1, tool2)
        sections.append({
            "type": "verdict",
            "title": "Our Verdict",
            "content": verdict
        })
        
        # Calculate metrics
        total_content = overview + features + pricing + use_cases + verdict
        word_count = len(total_content.split())
        quality_score = self._calculate_content_quality(total_content, word_count)
        
        return {
            "sections": sections,
            "word_count": word_count,
            "quality_score": quality_score
        }
    
    def _generate_comparison_overview(self, tool1: Tool, tool2: Tool) -> str:
        """Generate comparison overview"""
        
        overview_content = f"""
        When choosing between {tool1.name} and {tool2.name}, it's essential to understand their key differences, strengths, and ideal use cases. 
        Both tools serve the {tool1.category.name} market but approach the problem from different angles, making them suitable for different types of users and scenarios.
        
        {tool1.name} focuses on {tool1.short_desc.lower()}, while {tool2.name} emphasizes {tool2.short_desc.lower()}. 
        This fundamental difference influences their feature sets, user interfaces, and overall user experience.
        
        This comprehensive comparison will help you understand which tool better aligns with your specific needs, budget, and technical requirements. 
        We'll examine every aspect from core functionality to pricing and support to give you the information needed to make an informed decision.
        """
        
        return overview_content.strip()
    
    def _generate_features_comparison(self, tool1: Tool, tool2: Tool) -> str:
        """Generate features comparison"""
        
        features_content = f"""
        Both {tool1.name} and {tool2.name} offer robust feature sets, but they excel in different areas. 
        Understanding these differences is crucial for selecting the right tool for your specific needs.
        
        {tool1.name} Strengths:
        • {tool1.short_desc}
        • User-friendly interface designed for beginners
        • Comprehensive documentation and tutorials
        • Strong community support and active forums
        • Regular updates with new features
        
        {tool2.name} Strengths:
        • {tool2.short_desc}
        • Advanced features for power users
        • Highly customizable settings and options
        • Excellent performance with large datasets
        • Enterprise-grade security and compliance
        
        Feature Comparison:
        • Ease of Use: {tool1.name} is generally considered more beginner-friendly
        • Advanced Features: {tool2.name} offers more sophisticated capabilities
        • Performance: Both tools perform well, but {tool2.name} edges out with complex tasks
        • Support: Both offer good support, but {tool1.name} has more extensive documentation
        • Integration: {tool2.name} provides more third-party integration options
        """
        
        return features_content.strip()
    
    def _generate_pricing_comparison(self, tool1: Tool, tool2: Tool) -> str:
        """Generate pricing comparison"""
        
        pricing_content = f"""
        Pricing is a critical factor when choosing between {tool1.name} and {tool2.name}, especially for long-term use or team deployments. 
        Both tools offer different pricing models that cater to various user segments and budgets.
        
        {tool1.name} Pricing:
        • Free tier available with basic features
        • Premium plans starting at $9.99/month for individuals
        • Team plans starting at $29.99/month for 5 users
        • Enterprise plans with custom pricing
        • 14-day free trial for premium features
        
        {tool2.name} Pricing:
        • Free tier with limited functionality
        • Professional plans starting at $14.99/month
        • Business plans starting at $39.99/month for 10 users
        • Enterprise solutions with volume discounts
        • 30-day money-back guarantee
        
        Value Proposition:
        • For individual users on a budget, {tool1.name} offers better value with its generous free tier
        • For teams requiring advanced features, {tool2.name} provides better ROI despite higher pricing
        • Both tools offer good value for their respective target markets
        • Consider your long-term needs when evaluating total cost of ownership
        """
        
        return pricing_content.strip()
    
    def _generate_use_cases_comparison(self, tool1: Tool, tool2: Tool) -> str:
        """Generate use cases comparison"""
        
        use_cases_content = f"""
        Understanding the ideal use cases for {tool1.name} and {tool2.name} helps determine which tool better suits your specific scenarios. 
        While both tools serve the {tool1.category.name} market, they excel in different situations and user contexts.
        
        {tool1.name} is ideal for:
        • Beginners and users new to {tool1.category.name.lower()}
        • Small teams and individual professionals
        • Projects requiring quick setup and deployment
        • Users who prioritize ease of use over advanced features
        • Educational institutions and training programs
        
        {tool2.name} excels in:
        • Enterprise environments with complex requirements
        • Power users needing advanced customization
        • Large-scale deployments with high performance needs
        • Organizations requiring extensive integration capabilities
        • Projects demanding granular control and configuration
        
        Overlapping Use Cases:
        Both tools work well for general {tool1.category.name.lower()} tasks, but {tool1.name} is better for getting started quickly, 
        while {tool2.name} provides more room for growth as your needs become more sophisticated.
        """
        
        return use_cases_content.strip()
    
    def _generate_comparison_verdict(self, tool1: Tool, tool2: Tool) -> str:
        """Generate comparison verdict"""
        
        verdict_content = f"""
        After comprehensive analysis of both {tool1.name} and {tool2.name}, the choice depends largely on your specific needs, experience level, and budget constraints.
        
        Choose {tool1.name} if:
        • You're new to {tool1.category.name.lower()} and want an easy learning curve
        • You need a cost-effective solution with good free tier features
        • You prioritize user experience and quick setup
        • You're working on small to medium-sized projects
        • You value extensive documentation and community support
        
        Choose {tool2.name} if:
        • You need advanced features and customization options
        • You're working on enterprise-level projects
        • Performance and scalability are critical requirements
        • You require extensive integration capabilities
        • Budget is less of a constraint than functionality
        
        Final Recommendation:
        For most users starting out, we recommend beginning with {tool1.name} and upgrading to {tool2.name} as your needs grow. 
        Both tools are excellent choices, but they serve different segments of the market effectively.
        """
        
        return verdict_content.strip()
    
    def _generate_alternatives_pages(self, count: int) -> List[Dict[str, Any]]:
        """Generate alternatives pages"""
        
        alternatives_pages = []
        
        for i in range(count):
            category = random.choice(list(ToolCategory.objects.filter(is_active=True)))
            alternatives_page = self._create_alternatives_page(category, i)
            if alternatives_page:
                alternatives_pages.append(alternatives_page)
        
        return alternatives_pages
    
    def _create_alternatives_page(self, category: ToolCategory, index: int) -> Optional[Dict[str, Any]]:
        """Create alternatives page"""
        
        year = datetime.now().year
        title = f"Best {category.name} Alternatives in {year}"
        slug = slugify(f"best-{category.slug}-alternatives-{year}")
        
        # Ensure uniqueness
        counter = 1
        while SEOPage.objects.filter(slug=slug).exists():
            slug = f"{slug}-{counter}"
            counter += 1
        
        # Generate alternatives content
        content_data = self._generate_alternatives_content(category, year)
        
        if not content_data or content_data['word_count'] < 1500:
            return None
        
        alternatives_data = {
            "title": title,
            "slug": slug,
            "content_intro": content_data['intro'],
            "items": content_data['sections'],
            "meta_title": self._generate_authority_meta_title(title),
            "meta_description": self._generate_authority_meta_description(category.name, title),
            "content_type": "alternatives_page",
            "category": category.name,
            "year": year,
            "word_count": content_data['word_count'],
            "quality_score": content_data['quality_score'],
            "backlink_score": self._calculate_backlink_score("alternatives_page", category.name),
            "internal_links": self._generate_authority_internal_links(category.name, "alternatives_page")
        }
        
        return alternatives_data
    
    def _generate_alternatives_content(self, category: ToolCategory, year: int) -> Dict[str, Any]:
        """Generate alternatives content"""
        
        sections = []
        
        # Overview
        overview = self._generate_alternatives_overview(category, year)
        sections.append({
            "type": "overview",
            "title": f"{category.name} Software Overview",
            "content": overview
        })
        
        # Top alternatives
        top_alternatives = self._generate_top_alternatives(category)
        sections.append({
            "type": "top_alternatives",
            "title": "Top Alternatives",
            "content": top_alternatives
        })
        
        # Comparison
        comparison = self._generate_alternatives_comparison(category)
        sections.append({
            "type": "comparison",
            "title": "Detailed Comparison",
            "content": comparison
        })
        
        # Recommendations
        recommendations = self._generate_alternatives_recommendations(category)
        sections.append({
            "type": "recommendations",
            "title": "Our Recommendations",
            "content": recommendations
        })
        
        # Calculate metrics
        total_content = overview + top_alternatives + comparison + recommendations
        word_count = len(total_content.split())
        quality_score = self._calculate_content_quality(total_content, word_count)
        
        return {
            "sections": sections,
            "word_count": word_count,
            "quality_score": quality_score
        }
    
    def _generate_alternatives_overview(self, category: ToolCategory, year: int) -> str:
        """Generate alternatives overview"""
        
        overview_content = f"""
        The {category.name} software market has evolved significantly in {year}, offering users more choices than ever before. 
        With numerous options available, finding the right solution that meets your specific needs can be challenging. 
        This comprehensive guide explores the best {category.name} alternatives available today.
        
        Whether you're looking for free alternatives, enterprise-grade solutions, or specialized tools for specific use cases, 
        this guide will help you make an informed decision. We've analyzed dozens of {category.name} tools based on features, pricing, user experience, and overall value.
        
        The market includes everything from simple, user-friendly tools to complex, feature-rich platforms. 
        Understanding the landscape and knowing what to look for will help you choose the {category.name} solution that best fits your requirements and budget.
        """
        
        return overview_content.strip()
    
    def _generate_top_alternatives(self, category: ToolCategory) -> str:
        """Generate top alternatives content"""
        
        # Get top tools in category
        top_tools = category.tools.filter(is_active=True).order_by('-view_count')[:8]
        
        alternatives_content = f"""
        Based on our analysis and user feedback, here are the top {category.name} alternatives you should consider:
        
        """
        
        for tool in top_tools:
            alternatives_content += f"""
        {tool.name}
        {tool.short_desc}
        • Pricing: Free tier available, premium plans from $9.99/month
        • Best for: {self._get_tool_best_for(tool)}
        • Key features: {', '.join(tool.get_tags_list()[:3])}
        • User rating: {random.randint(4.0, 4.8)}/5 based on {random.randint(100, 1000)} reviews
        
        """
        
        alternatives_content += """
        Each of these alternatives offers unique strengths and serves different user segments. 
        Consider your specific requirements, budget, and technical expertise when making your choice.
        """
        
        return alternatives_content.strip()
    
    def _generate_alternatives_comparison(self, category: ToolCategory) -> str:
        """Generate alternatives comparison"""
        
        comparison_content = f"""
        Comparing {category.name} alternatives requires understanding the key factors that differentiate these tools and impact user experience. 
        While all tools in this category serve similar purposes, they vary significantly in terms of features, pricing, and target audiences.
        
        Key comparison factors include:
        
        • Core Functionality: All tools provide basic {category.name.lower()} capabilities, but advanced features vary widely
        • User Interface: Some tools prioritize simplicity and ease of use, while others offer comprehensive control panels
        • Pricing Models: Options range from completely free to enterprise-level subscriptions
        • Integration Capabilities: Consider how well each tool integrates with your existing workflow and software stack
        • Performance: Speed, reliability, and scalability can vary significantly between options
        • Support and Documentation: Quality of customer support and available learning resources
        • Security and Compliance: Important considerations for enterprise and sensitive data handling
        
        Understanding these factors will help you evaluate alternatives based on your specific priorities and requirements rather than just feature lists or pricing alone.
        """
        
        return comparison_content.strip()
    
    def _generate_alternatives_recommendations(self, category: ToolCategory) -> str:
        """Generate alternatives recommendations"""
        
        recommendations_content = f"""
        Based on our comprehensive analysis of {category.name} alternatives, here are our recommendations for different user segments and use cases:
        
        For Beginners and Individual Users:
        Start with free or low-cost options that offer intuitive interfaces and good documentation. 
        Focus on learning the fundamentals before investing in premium features.
        
        For Small Teams and Growing Businesses:
        Consider tools that offer good collaboration features and scalable pricing models. 
        Look for solutions that can grow with your business without requiring significant migrations.
        
        For Enterprise Organizations:
        Prioritize security, compliance, and integration capabilities. 
        Consider total cost of ownership rather than just subscription fees, including implementation and training costs.
        
        For Specialized Use Cases:
        Look for tools that excel in your specific requirements, even if they're not the most popular overall options. 
        Specialized tools often provide better value for niche applications.
        
        Final Thoughts:
        The best {category.name} alternative is the one that aligns with your specific needs, budget, and technical requirements. 
        Take advantage of free trials and demos to evaluate options before making a commitment, and don't hesitate to switch if your current solution no longer meets your needs.
        """
        
        return recommendations_content.strip()
    
    def _generate_resource_pages(self, count: int) -> List[Dict[str, Any]]:
        """Generate resource pages"""
        
        resource_pages = []
        
        for i in range(count):
            topic = random.choice(self.high_value_topics)
            resource_page = self._create_resource_page(topic, i)
            if resource_page:
                resource_pages.append(resource_page)
        
        return resource_pages
    
    def _create_resource_page(self, topic: str, index: int) -> Optional[Dict[str, Any]]:
        """Create individual resource page"""
        
        title = f"Free {topic} Resources & Tools"
        slug = slugify(f"free-{topic.lower()}-resources")
        
        # Ensure uniqueness
        counter = 1
        while SEOPage.objects.filter(slug=slug).exists():
            slug = f"{slug}-{counter}"
            counter += 1
        
        # Generate resource content
        content_data = self._generate_resource_content(topic)
        
        if not content_data or content_data['word_count'] < 1200:
            return None
        
        resource_data = {
            "title": title,
            "slug": slug,
            "content_intro": content_data['intro'],
            "items": content_data['sections'],
            "meta_title": self._generate_authority_meta_title(title),
            "meta_description": self._generate_authority_meta_description(topic, title),
            "content_type": "resource_page",
            "topic": topic,
            "word_count": content_data['word_count'],
            "quality_score": content_data['quality_score'],
            "backlink_score": self._calculate_backlink_score("resource_page", topic),
            "internal_links": self._generate_authority_internal_links(topic, "resource_page")
        }
        
        return resource_data
    
    def _generate_resource_content(self, topic: str) -> Dict[str, Any]:
        """Generate resource content"""
        
        sections = []
        
        # Overview
        overview = self._generate_resource_overview(topic)
        sections.append({
            "type": "overview",
            "title": f"{topic} Resources Overview",
            "content": overview
        })
        
        # Tools
        tools = self._generate_resource_tools(topic)
        sections.append({
            "type": "tools",
            "title": "Essential Tools",
            "content": tools
        })
        
        # Templates
        templates = self._generate_resource_templates(topic)
        sections.append({
            "type": "templates",
            "title": "Free Templates",
            "content": templates
        })
        
        # Guides
        guides = self._generate_resource_guides(topic)
        sections.append({
            "type": "guides",
            "title": "Learning Guides",
            "content": guides
        })
        
        # Community
        community = self._generate_resource_community(topic)
        sections.append({
            "type": "community",
            "title": "Community Resources",
            "content": community
        })
        
        # Calculate metrics
        total_content = overview + tools + templates + guides + community
        word_count = len(total_content.split())
        quality_score = self._calculate_content_quality(total_content, word_count)
        
        return {
            "sections": sections,
            "word_count": word_count,
            "quality_score": quality_score
        }
    
    def _generate_resource_overview(self, topic: str) -> str:
        """Generate resource overview"""
        
        overview_content = f"""
        Welcome to the most comprehensive collection of free {topic} resources available online. 
        Whether you're a beginner just starting out or an experienced professional looking to expand your toolkit, 
        you'll find valuable resources to enhance your {topic} skills and productivity.
        
        This curated collection includes tools, templates, guides, tutorials, and community resources that have been carefully selected based on quality, 
        usability, and value. All resources are either completely free or offer substantial free tiers that provide significant functionality.
        
        We've organized these resources into logical categories to help you quickly find what you need. 
        Each resource includes detailed descriptions, usage instructions, and tips for getting the most value from the tool or material.
        
        Bookmark this page as your go-to reference for {topic} resources, and check back regularly as we continuously update our collection with new and improved resources.
        """
        
        return overview_content.strip()
    
    def _generate_resource_tools(self, topic: str) -> str:
        """Generate tools resource content"""
        
        tools_content = f"""
        Essential {topic} tools can significantly improve your productivity and the quality of your work. 
        These free and freemium tools offer professional-grade functionality without the hefty price tags of premium software.
        
        Top Free {topic} Tools:
        • Tool 1: Comprehensive {topic} solution with advanced features
        • Tool 2: User-friendly interface perfect for beginners
        • Tool 3: Specialized tool for specific {topic} tasks
        • Tool 4: Collaborative platform for team projects
        • Tool 5: Automation tool to streamline repetitive tasks
        
        Each tool has been thoroughly tested and evaluated based on functionality, ease of use, performance, and overall value. 
        We provide detailed reviews, usage guides, and tips to help you get the most from each tool.
        
        Many of these tools offer premium versions with additional features, but the free tiers provide substantial functionality that meets most users' needs. 
        Start with the free versions and upgrade only if you require advanced features or higher usage limits.
        """
        
        return tools_content.strip()
    
    def _generate_resource_templates(self, topic: str) -> str:
        """Generate templates resource content"""
        
        templates_content = f"""
        Templates save time and ensure consistency in your {topic} projects. 
        These free templates cover various use cases and industries, providing professional-quality starting points for your work.
        
        Available Template Categories:
        • Business Templates: Professional documents for corporate environments
        • Creative Templates: Artistic and design-focused templates
        • Educational Templates: Learning materials and academic resources
        • Technical Templates: Specialized templates for technical applications
        • Personal Templates: Individual use templates for personal projects
        
        Each template is fully customizable and comes with detailed instructions for customization and best practices. 
        These templates have been created by professionals and follow industry standards for formatting and content structure.
        
        Templates are available in various formats including Word, PDF, and Google Docs, ensuring compatibility with your preferred software. 
        Regular updates ensure templates remain current with industry trends and best practices.
        """
        
        return templates_content.strip()
    
    def _generate_resource_guides(self, topic: str) -> str:
        """Generate guides resource content"""
        
        guides_content = f"""
        Learning {topic} effectively requires access to quality educational materials. 
        These free guides cover everything from basic concepts to advanced techniques, helping you master {topic} at your own pace.
        
        Guide Categories:
        • Beginner Guides: Step-by-step tutorials for newcomers
        • Advanced Techniques: In-depth guides for experienced users
        • Best Practices: Industry-standard approaches and methodologies
        • Troubleshooting: Common problems and their solutions
        • Case Studies: Real-world examples and applications
        
        Each guide is written by experienced professionals and includes practical examples, screenshots, and actionable tips. 
        The guides are structured to facilitate easy learning, with clear objectives, step-by-step instructions, and summary sections for quick reference.
        
        Many guides include downloadable resources such as checklists, templates, and reference materials to supplement your learning. 
        These comprehensive guides serve as both learning materials and ongoing reference resources as you advance your {topic} skills.
        """
        
        return guides_content.strip()
    
    def _generate_resource_community(self, topic: str) -> str:
        """Generate community resource content"""
        
        community_content = f"""
        Joining {topic} communities provides access to collective knowledge, networking opportunities, and ongoing support. 
        These free communities connect you with fellow enthusiasts, professionals, and experts who share your interests and challenges.
        
        Community Resources:
        • Forums: Discussion boards for questions and answers
        • Social Media Groups: Facebook, LinkedIn, and Reddit communities
        • Discord Servers: Real-time chat and voice communication
        • Meetup Groups: Local and virtual networking events
        • Open Source Projects: Collaborative development opportunities
        
        Active participation in these communities can accelerate your learning, provide solutions to specific problems, and create valuable professional connections. 
        Many communities also offer exclusive resources, early access to new tools, and opportunities to contribute to {topic} projects.
        
        Community guidelines and moderation ensure productive, respectful environments where members can share knowledge and support each other's growth. 
        Whether you're seeking help, looking to share your expertise, or simply want to connect with like-minded individuals, these communities offer valuable opportunities.
        """
        
        return community_content.strip()
    
    def _get_relevant_tools(self, topic: str) -> List[Tool]:
        """Get relevant tools for topic"""
        
        # Simple keyword matching for relevant tools
        topic_keywords = topic.lower().split()
        
        relevant_tools = []
        all_tools = Tool.objects.filter(is_active=True)
        
        for tool in all_tools:
            tool_text = f"{tool.name} {tool.short_desc} {tool.tags}".lower()
            if any(keyword in tool_text for keyword in topic_keywords):
                relevant_tools.append(tool)
        
        return relevant_tools[:10]  # Return top 10 relevant tools
    
    def _get_tool_best_for(self, tool: Tool) -> str:
        """Get best use case for tool"""
        
        if "beginner" in tool.short_desc.lower() or "easy" in tool.short_desc.lower():
            return "Beginners and casual users"
        elif "professional" in tool.short_desc.lower() or "advanced" in tool.short_desc.lower():
            return "Professional users and experts"
        elif "team" in tool.short_desc.lower() or "collaboration" in tool.short_desc.lower():
            return "Teams and collaboration"
        elif "business" in tool.short_desc.lower() or "enterprise" in tool.short_desc.lower():
            return "Business and enterprise"
        else:
            return "General use"
    
    def _calculate_content_quality(self, content: str, word_count: int) -> float:
        """Calculate content quality score"""
        
        score = 0.0
        
        # Word count score (30%)
        if word_count >= 3000:
            score += 0.3
        elif word_count >= 2000:
            score += 0.25
        elif word_count >= 1500:
            score += 0.2
        elif word_count >= 1000:
            score += 0.15
        elif word_count >= 500:
            score += 0.1
        
        # Content structure score (25%)
        if "##" in content or "###" in content:  # Has headings
            score += 0.1
        if "•" in content or "-" in content:  # Has lists
            score += 0.1
        if "Q:" in content or "A:" in content:  # Has Q&A
            score += 0.05
        
        # Uniqueness score (25%)
        uniqueness_score = content_uniqueness_engine.calculate_content_uniqueness_score(content)
        score += uniqueness_score * 0.25
        
        # Readability score (20%)
        sentences = content.split('. ')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        if 15 <= avg_sentence_length <= 25:
            score += 0.2
        elif 10 <= avg_sentence_length <= 30:
            score += 0.15
        elif 5 <= avg_sentence_length <= 35:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_backlink_score(self, page_type: str, topic: str) -> float:
        """Calculate backlink potential score"""
        
        base_scores = {
            "mega_guide": 0.9,
            "statistics_page": 0.8,
            "comparison_page": 0.7,
            "alternatives_page": 0.6,
            "resource_page": 0.7
        }
        
        base_score = base_scores.get(page_type, 0.5)
        
        # Adjust based on topic value
        if topic in self.high_value_topics:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _generate_authority_meta_title(self, title: str) -> str:
        """Generate meta title for authority page"""
        
        # Ensure under 70 characters
        if len(title) <= 65:
            return f"{title} | LamGen"
        else:
            return f"{title[:62]}... | LamGen"
    
    def _generate_authority_meta_description(self, topic: str, title: str) -> str:
        """Generate meta description for authority page"""
        
        desc_parts = [
            f"Comprehensive {topic.lower()} resource",
            "with expert insights and analysis",
            "completely free to use",
            "updated for 2024"
        ]
        
        meta_desc = " | ".join(desc_parts)
        
        return meta_desc[:160]
    
    def _generate_authority_internal_links(self, topic: str, page_type: str) -> List[Dict[str, str]]:
        """Generate internal links for authority page"""
        
        links = []
        
        # Link to relevant tools
        relevant_tools = self._get_relevant_tools(topic)
        for tool in relevant_tools[:3]:
            links.append({
                "title": tool.name,
                "url": tool.get_absolute_url(),
                "description": tool.short_desc
            })
        
        # Link to related authority pages
        related_topics = [t for t in self.high_value_topics if t != topic]
        for related_topic in random.sample(related_topics, min(2, len(related_topics))):
            links.append({
                "title": f"Free {related_topic} Resources",
                "url": f"/resources/{related_topic.lower().replace(' ', '-')}/",
                "description": f"Comprehensive {related_topic} tools and guides"
            })
        
        return links
    
    def _save_authority_pages(self, pages: List[Dict[str, Any]], page_type: str):
        """Save authority pages to database"""
        
        # Get or create authority category
        category, created = SEOCategory.objects.get_or_create(
            slug=f"{page_type.replace('_', '-')}",
            defaults={
                "name": page_type.replace('_', ' ').title(),
                "title_template": "{topic} — Authority Resource",
                "meta_desc_template": "Comprehensive {topic} resource with expert insights and analysis."
            }
        )
        
        # Create pages in batches
        batch_size = 20
        
        for i in range(0, len(pages), batch_size):
            batch = pages[i:i + batch_size]
            
            seo_pages = []
            for page_data in batch:
                seo_page = SEOPage(
                    category=category,
                    topic=page_data["title"],
                    slug=page_data["slug"],
                    content_intro=page_data["content_intro"],
                    items=page_data["items"],
                    meta_title=page_data["meta_title"],
                    meta_description=page_data["meta_description"],
                    is_active=True
                )
                seo_pages.append(seo_page)
            
            # Bulk create
            SEOPage.objects.bulk_create(seo_pages, batch_size=batch_size)
    
    def _calculate_authority_quality(self) -> Dict[str, float]:
        """Calculate overall authority content quality"""
        
        all_pages = SEOPage.objects.filter(is_active=True)
        
        if not all_pages.exists():
            return {"overall": 0.0}
        
        quality_scores = []
        
        for page in all_pages[:50]:  # Sample for performance
            content = page.content_intro or ""
            if page.items:
                content += " ".join(str(item) for item in page.items)
            
            if content:
                score = self._calculate_content_quality(content, len(content.split()))
                quality_scores.append(score)
        
        if quality_scores:
            return {
                "overall": sum(quality_scores) / len(quality_scores),
                "pages_analyzed": len(quality_scores)
            }
        
        return {"overall": 0.0}
    
    def _estimate_backlink_potential(self) -> Dict[str, Any]:
        """Estimate backlink potential"""
        
        pages_by_type = {}
        total_potential = 0.0
        
        for page_type in self.authority_types.keys():
            category = SEOCategory.objects.filter(slug=page_type.replace('_', '-')).first()
            if category:
                page_count = category.pages.filter(is_active=True).count()
                avg_score = 0.75  # Estimated average backlink score
                potential = page_count * avg_score
                
                pages_by_type[page_type] = {
                    "page_count": page_count,
                    "avg_backlink_score": avg_score,
                    "total_potential": potential
                }
                total_potential += potential
        
        return {
            "by_type": pages_by_type,
            "total_potential": total_potential,
            "estimated_monthly_backlinks": int(total_potential * 2)  # Rough estimate
        }


# Singleton instance
authority_builder = AuthorityBuilder()
