"""
Tool Output Indexing System
Creates public indexable pages for generated content (resumes, bios, prompts, etc.)
"""

from typing import List, Dict, Any, Optional
from django.db.models import Q, Count, F
from django.utils.text import slugify
from django.core.cache import cache
from django.conf import settings
from apps.tools.models import Tool, ToolCategory
from apps.seo.models import SEOCategory, SEOPage
import json
import hashlib
from datetime import datetime, timedelta
import random


class ToolOutputIndexer:
    """Advanced tool output indexing for public SEO pages"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 12  # 12 hours
        self.content_types = {
            'resumes': {
                'category_slug': 'generated-resumes',
                'category_name': 'Generated Resumes',
                'base_path': '/examples/resumes/',
                'template': 'resume',
                'schema_type': 'CreativeWork'
            },
            'bios': {
                'category_slug': 'generated-bios',
                'category_name': 'Generated Bios',
                'base_path': '/examples/bios/',
                'template': 'bio',
                'schema_type': 'Article'
            },
            'prompts': {
                'category_slug': 'generated-prompts',
                'category_name': 'Generated Prompts',
                'base_path': '/examples/prompts/',
                'template': 'prompt',
                'schema_type': 'CreativeWork'
            },
            'chats': {
                'category_slug': 'generated-chats',
                'category_name': 'Generated Chats',
                'base_path': '/examples/chats/',
                'template': 'chat',
                'schema_type': 'DiscussionForumPosting'
            },
            'templates': {
                'category_slug': 'generated-templates',
                'category_name': 'Generated Templates',
                'base_path': '/templates/',
                'template': 'template',
                'schema_type': 'WebPage'
            }
        }
        
        self.industry_contexts = [
            'technology', 'healthcare', 'finance', 'education', 'marketing',
            'retail', 'manufacturing', 'consulting', 'legal', 'real-estate'
        ]
        
        self.experience_levels = [
            'entry-level', 'mid-level', 'senior', 'executive', 'freshers'
        ]
        
        self.style_variations = [
            'professional', 'creative', 'modern', 'classic', 'minimal'
        ]
    
    def index_generated_content(self, content_type: str, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index generated content for public SEO pages"""
        
        if content_type not in self.content_types:
            return {"error": f"Unsupported content type: {content_type}"}
        
        indexing_report = {
            "content_type": content_type,
            "sample_count": len(sample_data),
            "indexed_pages": 0,
            "categories_created": 0,
            "internal_links_created": 0,
            "quality_score": 0.0
        }
        
        # Create or get content category
        category = self._get_or_create_content_category(content_type)
        if category:
            indexing_report["categories_created"] = 1
        
        # Process sample data
        indexed_pages = []
        for i, sample in enumerate(sample_data):
            page_data = self._create_indexed_page(sample, content_type, category, i)
            if page_data:
                indexed_pages.append(page_data)
        
        # Save indexed pages
        if indexed_pages:
            self._save_indexed_pages(indexed_pages)
            indexing_report["indexed_pages"] = len(indexed_pages)
        
        # Calculate quality score
        indexing_report["quality_score"] = self._calculate_indexing_quality(indexed_pages)
        
        return indexing_report
    
    def _get_or_create_content_category(self, content_type: str):
        """Get or create content category for indexing"""
        
        config = self.content_types[content_type]
        
        category, created = SEOCategory.objects.get_or_create(
            slug=config['category_slug'],
            defaults={
                "name": config['category_name'],
                "title_template": "{topic} — Generated Example",
                "meta_desc_template": "Professional {topic} example with best practices and guidelines.",
                "schema_type": config['schema_type']
            }
        )
        
        return category
    
    def _create_indexed_page(self, sample: Dict[str, Any], content_type: str, category, index: int) -> Optional[Dict[str, Any]]:
        """Create indexed page from sample data"""
        
        config = self.content_types[content_type]
        
        # Generate unique title and slug
        title = self._generate_sample_title(sample, content_type, index)
        slug = self._generate_sample_slug(title, content_type, index)
        
        # Generate comprehensive content
        content_data = self._generate_sample_content(sample, content_type, title)
        
        if not content_data or content_data['word_count'] < 200:
            return None
        
        # Create page data
        page_data = {
            "category": category,
            "topic": title,
            "slug": slug,
            "content_intro": content_data['intro'],
            "items": content_data['examples'],
            "meta_title": self._generate_sample_meta_title(title, content_type),
            "meta_description": self._generate_sample_meta_description(sample, content_type),
            "is_active": True,
            "sample_data": sample,
            "content_type": content_type,
            "quality_score": content_data['quality_score'],
            "internal_links": self._generate_sample_internal_links(content_type, title)
        }
        
        return page_data
    
    def _generate_sample_title(self, sample: Dict[str, Any], content_type: str, index: int) -> str:
        """Generate unique title for sample"""
        
        config = self.content_types[content_type]
        
        # Extract context from sample
        context = self._extract_sample_context(sample)
        
        # Base title patterns
        if content_type == 'resumes':
            title_patterns = [
                f"Professional Resume Example for {context}",
                f"{context.title()} Resume Sample",
                f"Best Resume Template for {context}",
                f"Complete {context.title()} Resume Guide"
            ]
        elif content_type == 'bios':
            title_patterns = [
                f"Professional Bio Example for {context}",
                f"{context.title()} Biography Sample",
                f"Compelling Bio Template for {context}",
                f"Complete {context.title()} Bio Guide"
            ]
        elif content_type == 'prompts':
            title_patterns = [
                f"Effective Writing Prompts for {context}",
                f"{context.title()} Prompt Examples",
                f"Creative Writing Ideas for {context}",
                f"Best Prompts for {context}"
            ]
        elif content_type == 'chats':
            title_patterns = [
                f"Chat Conversation Example for {context}",
                f"{context.title()} Dialogue Sample",
                f"Professional Chat Template for {context}",
                f"Complete {context.title()} Chat Guide"
            ]
        elif content_type == 'templates':
            title_patterns = [
                f"Professional Template for {context}",
                f"{context.title()} Template Example",
                f"Complete {context.title()} Template",
                f"Best Template for {context}"
            ]
        else:
            title_patterns = [
                f"Example for {context}",
                f"{context.title()} Sample",
                f"Template for {context}",
                f"Guide for {context}"
            ]
        
        # Add variation to ensure uniqueness
        base_title = random.choice(title_patterns)
        
        # Add index if needed for uniqueness
        if index > 100:
            title = f"{base_title} ({index})"
        else:
            title = base_title
        
        return title
    
    def _generate_sample_slug(self, title: str, content_type: str, index: int) -> str:
        """Generate unique slug for sample"""
        
        base_slug = slugify(title)
        
        # Ensure uniqueness
        counter = 1
        slug = base_slug
        while SEOPage.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def _extract_sample_context(self, sample: Dict[str, Any]) -> str:
        """Extract context from sample data"""
        
        # Try to extract from sample data
        if 'industry' in sample:
            return sample['industry']
        elif 'profession' in sample:
            return sample['profession']
        elif 'role' in sample:
            return sample['role']
        elif 'title' in sample:
            return sample['title']
        elif 'category' in sample:
            return sample['category']
        else:
            # Use random context
            return random.choice(self.industry_contexts)
    
    def _generate_sample_content(self, sample: Dict[str, Any], content_type: str, title: str) -> Dict[str, Any]:
        """Generate comprehensive content for sample"""
        
        context = self._extract_sample_context(sample)
        
        # Generate introduction
        intro = self._generate_sample_intro(sample, content_type, title, context)
        
        # Generate examples
        examples = self._generate_sample_examples(sample, content_type, context)
        
        # Generate benefits
        benefits = self._generate_sample_benefits(content_type, context)
        
        # Generate steps
        steps = self._generate_sample_steps(content_type, context)
        
        # Calculate metrics
        word_count = len(intro.split()) + sum(len(ex.split()) for ex in examples)
        quality_score = self._calculate_sample_quality(intro, examples, benefits)
        
        return {
            "intro": intro,
            "examples": examples,
            "benefits": benefits,
            "steps": steps,
            "word_count": word_count,
            "quality_score": quality_score
        }
    
    def _generate_sample_intro(self, sample: Dict[str, Any], content_type: str, title: str, context: str) -> str:
        """Generate introduction for sample"""
        
        config = self.content_types[content_type]
        
        intro_parts = []
        
        # Opening statement
        intro_parts.append(f"Discover this professional {config['template']} example designed specifically for {context} professionals.")
        
        # Context explanation
        intro_parts.append(f"This comprehensive example showcases best practices and industry standards for {context} roles, providing a clear template you can adapt for your needs.")
        
        # Key features
        intro_parts.append(f"Our {config['template']} includes all essential elements: professional formatting, industry-specific terminology, and proven structures that resonate with hiring managers and recruiters.")
        
        # Usage guidance
        intro_parts.append(f"Use this example as a foundation to create your own professional {config['template']} that highlights your unique skills and experience in the {context} field.")
        
        return " ".join(intro_parts)
    
    def _generate_sample_examples(self, sample: Dict[str, Any], content_type: str, context: str) -> List[str]:
        """Generate example content"""
        
        examples = []
        
        if content_type == 'resumes':
            examples = [
                "Professional summary highlighting key achievements and skills",
                "Work experience section with quantified accomplishments",
                "Education and certifications relevant to the role",
                "Skills section with technical and soft competencies"
            ]
        elif content_type == 'bios':
            examples = [
                "Compelling opening statement establishing expertise",
                "Professional background and career progression",
                "Key achievements and notable projects",
                "Personal touch and future aspirations"
            ]
        elif content_type == 'prompts':
            examples = [
                "Creative writing prompts for inspiration",
                "Professional development prompts",
                "Problem-solving scenarios",
                "Industry-specific discussion topics"
            ]
        elif content_type == 'chats':
            examples = [
                "Professional conversation structure",
                "Industry-specific terminology and jargon",
                "Problem-solving dialogue examples",
                "Customer interaction patterns"
            ]
        elif content_type == 'templates':
            examples = [
                "Professional layout and formatting",
                "Industry-standard sections and headers",
                "Customizable content placeholders",
                "Best practice guidelines and tips"
            ]
        
        return examples
    
    def _generate_sample_benefits(self, content_type: str, context: str) -> List[str]:
        """Generate benefits for sample"""
        
        benefits = [
            f"Industry-standard formatting for {context} professionals",
            "Time-tested structure that gets results",
            "Customizable template for personalization",
            "Professional appearance and presentation",
            "Comprehensive coverage of essential elements"
        ]
        
        return benefits
    
    def _generate_sample_steps(self, content_type: str, context: str) -> List[Dict[str, str]]:
        """Generate usage steps"""
        
        steps = [
            {
                "title": "Step 1: Review the Example",
                "content": f"Carefully study this {content_type[:-1]} example to understand the structure and content."
            },
            {
                "title": "Step 2: Customize Content",
                "content": f"Adapt the content to reflect your specific {context} experience and skills."
            },
            {
                "title": "Step 3: Optimize Format",
                "content": "Ensure proper formatting and professional presentation."
            },
            {
                "title": "Step 4: Review and Refine",
                "content": "Proofread carefully and make final adjustments."
            }
        ]
        
        return steps
    
    def _generate_sample_meta_title(self, title: str, content_type: str) -> str:
        """Generate meta title for sample"""
        
        config = self.content_types[content_type]
        
        # Add power words
        power_words = ["Professional", "Complete", "Best", "Ultimate"]
        power_word = random.choice(power_words)
        
        meta_title = f"{power_word} {title} | LamGen"
        
        # Ensure under 70 characters
        return meta_title[:70]
    
    def _generate_sample_meta_description(self, sample: Dict[str, Any], content_type: str) -> str:
        """Generate meta description for sample"""
        
        context = self._extract_sample_context(sample)
        config = self.content_types[content_type]
        
        desc_parts = [
            f"Professional {config['template']} example for {context}",
            "with best practices and industry standards",
            "completely free to use and customize",
            "instant download and editing"
        ]
        
        meta_desc = " | ".join(desc_parts)
        
        return meta_desc[:160]
    
    def _generate_sample_internal_links(self, content_type: str, title: str) -> List[Dict[str, str]]:
        """Generate internal links for sample"""
        
        links = []
        
        # Link to related tools
        related_tools = self._get_related_tools_for_content(content_type)
        for tool in related_tools[:3]:
            links.append({
                "title": tool.name,
                "url": tool.get_absolute_url(),
                "description": tool.short_desc
            })
        
        # Link to related samples
        links.append({
            "title": f"More {content_type.title()} Examples",
            "url": f"/examples/{content_type}/",
            "description": f"Browse more professional {content_type} examples"
        })
        
        return links
    
    def _get_related_tools_for_content(self, content_type: str) -> List[Tool]:
        """Get tools related to content type"""
        
        tool_mapping = {
            'resumes': ['Resume Builder', 'Resume Summary', 'Resume Formatter'],
            'bios': ['Bio Generator', 'Professional Bio', 'Personal Bio'],
            'prompts': ['Writing Prompts', 'Creative Writing', 'AI Prompts'],
            'chats': ['Chat Generator', 'Fake Chat', 'Conversation Creator'],
            'templates': ['Template Generator', 'Document Template', 'Professional Template']
        }
        
        tool_names = tool_mapping.get(content_type, [])
        
        return Tool.objects.filter(name__in=tool_names, is_active=True)
    
    def _calculate_sample_quality(self, intro: str, examples: List[str], benefits: List[str]) -> float:
        """Calculate quality score for sample"""
        
        score = 0.0
        
        # Intro quality (40%)
        intro_words = len(intro.split())
        if intro_words >= 100:
            score += 0.4
        elif intro_words >= 75:
            score += 0.3
        elif intro_words >= 50:
            score += 0.2
        
        # Examples quality (35%)
        if len(examples) >= 4:
            score += 0.35
        elif len(examples) >= 3:
            score += 0.25
        elif len(examples) >= 2:
            score += 0.15
        
        # Benefits quality (25%)
        if len(benefits) >= 5:
            score += 0.25
        elif len(benefits) >= 3:
            score += 0.15
        elif len(benefits) >= 2:
            score += 0.1
        
        return min(score, 1.0)
    
    def _save_indexed_pages(self, pages: List[Dict[str, Any]]):
        """Save indexed pages to database"""
        
        # Create pages in batches
        batch_size = 50
        
        for i in range(0, len(pages), batch_size):
            batch = pages[i:i + batch_size]
            
            seo_pages = []
            for page_data in batch:
                seo_page = SEOPage(
                    category=page_data['category'],
                    topic=page_data['topic'],
                    slug=page_data['slug'],
                    content_intro=page_data['content_intro'],
                    items=page_data['examples'],
                    meta_title=page_data['meta_title'],
                    meta_description=page_data['meta_description'],
                    is_active=page_data['is_active']
                )
                seo_pages.append(seo_page)
            
            # Bulk create
            SEOPage.objects.bulk_create(seo_pages, batch_size=batch_size)
    
    def _calculate_indexing_quality(self, indexed_pages: List[Dict[str, Any]]) -> float:
        """Calculate overall indexing quality"""
        
        if not indexed_pages:
            return 0.0
        
        total_quality = sum(page.get('quality_score', 0) for page in indexed_pages)
        return total_quality / len(indexed_pages)
    
    def generate_sample_data(self, content_type: str, count: int = 100) -> List[Dict[str, Any]]:
        """Generate sample data for testing"""
        
        samples = []
        
        for i in range(count):
            sample = self._create_sample_data(content_type, i)
            samples.append(sample)
        
        return samples
    
    def _create_sample_data(self, content_type: str, index: int) -> Dict[str, Any]:
        """Create sample data instance"""
        
        # Random context
        context = random.choice(self.industry_contexts)
        experience = random.choice(self.experience_levels)
        style = random.choice(self.style_variations)
        
        if content_type == 'resumes':
            return {
                "name": f"John Doe {index}",
                "profession": f"Software Engineer",
                "industry": context,
                "experience": experience,
                "style": style,
                "summary": f"Experienced {experience} software engineer in {context} industry",
                "skills": ["Python", "JavaScript", "React", "Docker"],
                "experience_years": random.randint(2, 15)
            }
        elif content_type == 'bios':
            return {
                "name": f"Jane Smith {index}",
                "profession": f"Marketing Manager",
                "industry": context,
                "experience": experience,
                "style": style,
                "bio": f"Professional {experience} marketing manager with expertise in {context}",
                "achievements": ["Increased ROI by 300%", "Led team of 10", "Managed $2M budget"]
            }
        elif content_type == 'prompts':
            return {
                "category": context,
                "difficulty": experience,
                "style": style,
                "prompt": f"Write about {context} challenges for {experience} professionals",
                "word_count": random.randint(200, 800),
                "type": "creative"
            }
        elif content_type == 'chats':
            return {
                "platform": random.choice(["WhatsApp", "Instagram", "Telegram"]),
                "style": style,
                "context": context,
                "participants": 2,
                "messages": random.randint(10, 50),
                "topic": f"Discussion about {context} trends"
            }
        elif content_type == 'templates':
            return {
                "type": context,
                "style": style,
                "purpose": experience,
                "sections": ["Header", "Content", "Footer"],
                "customizable": True,
                "format": "document"
            }
        
        return {}
    
    def get_indexing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive indexing statistics"""
        
        stats = {
            "total_indexed_pages": SEOPage.objects.filter(is_active=True).count(),
            "content_type_breakdown": {},
            "quality_distribution": {},
            "recent_indexing": [],
            "top_performing_pages": [],
            "internal_link_coverage": 0.0
        }
        
        # Breakdown by content type
        for content_type, config in self.content_types.items():
            category = SEOCategory.objects.filter(slug=config['category_slug']).first()
            if category:
                page_count = category.pages.filter(is_active=True).count()
                stats["content_type_breakdown"][content_type] = page_count
        
        # Quality distribution
        all_pages = SEOPage.objects.filter(is_active=True)
        high_quality = all_pages.count()  # Simplified - would need actual quality scoring
        stats["quality_distribution"] = {
            "high_quality": high_quality,
            "medium_quality": 0,
            "low_quality": 0
        }
        
        # Recent indexing
        recent_pages = SEOPage.objects.filter(is_active=True).order_by('-created_at')[:10]
        stats["recent_indexing"] = [
            {
                "title": page.topic,
                "created_at": page.created_at,
                "category": page.category.name
            }
            for page in recent_pages
        ]
        
        return stats


# Singleton instance
tool_output_indexer = ToolOutputIndexer()
