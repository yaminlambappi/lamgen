"""
User-Generated Content Indexer for SEO
Creates indexable pages from tool outputs for organic traffic growth
"""

from typing import List, Dict, Any, Optional
from django.db.models import Q
from django.core.cache import cache
from tools.models import Tool, ToolCategory
from seo.models import SEOPage
import json
import hashlib
import re


class UserContentIndexer:
    """Index user-generated content for SEO benefits"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60  # 1 hour
        self.content_types = {
            'resume': 'Generated Resumes',
            'bio': 'Professional Bios', 
            'prompt': 'AI Prompts',
            'chat': 'Chat Conversations',
            'template': 'Document Templates',
            'example': 'Tool Examples',
            'guide': 'How-To Guides'
        }
        
    def index_tool_output(self, tool: Tool, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Index tool output as SEO page"""
        
        content_type = content_data.get('type', 'example')
        content_text = content_data.get('content', '')
        title = content_data.get('title', f'{tool.name} Example')
        
        # Generate unique identifier
        content_hash = hashlib.md5(
            f"{tool.id}_{content_type}_{content_text[:100]}".encode()
        ).hexdigest()[:16]
        
        # Create SEO-optimized page data
        seo_page_data = {
            'tool': tool,
            'content_hash': content_hash,
            'content_type': content_type,
            'title': title,
            'content': content_text,
            'meta_title': self._generate_meta_title(tool, content_data),
            'meta_description': self._generate_meta_description(tool, content_data),
            'seo_intro': self._generate_seo_intro(tool, content_data),
            'use_cases': self._generate_use_cases(tool, content_data),
            'faq_items': self._generate_faq_items(tool, content_data),
            'keywords': self._extract_keywords(tool, content_data),
            'word_count': len(content_text.split()),
            'quality_score': self._calculate_quality_score(content_data),
            'is_indexable': self._should_index(content_data)
        }
        
        return seo_page_data
    
    def create_content_category_pages(self, content_type: str) -> List[Dict[str, Any]]:
        """Create category pages for specific content types"""
        
        category_data = []
        
        # Get all tools that generate this content type
        relevant_tools = Tool.objects.filter(
            is_active=True,
            tags__icontains=content_type
        ).select_related('category')
        
        for tool in relevant_tools:
            # Create category page for this tool + content type
            category_page = {
                'tool': tool,
                'content_type': content_type,
                'title': f'{self.content_types.get(content_type, content_type.title())} for {tool.name}',
                'slug': f'{content_type}-{tool.slug}',
                'meta_title': f'Free {self.content_types.get(content_type, content_type.title())} for {tool.name} | LamGen',
                'meta_description': f'Generate professional {content_type} using {tool.name}. Free online tool with examples, templates, and instant results.',
                'seo_intro': f'{self.content_types.get(content_type, content_type.title())} for {tool.name} is a comprehensive resource that helps users create professional {content_type} instantly. Whether you need examples, templates, or complete generated content, our tool provides high-quality results with no registration required.',
                'use_cases': self._generate_category_use_cases(tool, content_type),
                'faq_items': self._generate_category_faq_items(tool, content_type),
                'keywords': [content_type, tool.name.lower(), 'free', 'online', 'generator'],
                'featured_examples': self._get_featured_examples(tool, content_type),
                'template_count': self._count_available_templates(tool, content_type)
            }
            category_data.append(category_page)
        
        return category_data
    
    def create_industry_specific_pages(self, tool: Tool) -> List[Dict[str, Any]]:
        """Create industry-specific content pages"""
        
        industries = [
            'healthcare', 'finance', 'technology', 'education', 
            'marketing', 'retail', 'manufacturing', 'consulting',
            'legal', 'real-estate', 'startup', 'enterprise'
        ]
        
        industry_pages = []
        
        for industry in industries:
            industry_page = {
                'tool': tool,
                'industry': industry,
                'title': f'{tool.name} for {industry.title()} Industry',
                'slug': f'{tool.slug}-for-{industry}',
                'meta_title': f'Free {tool.name} for {industry.title()} | Industry-Specific Tool | LamGen',
                'meta_description': f'Specialized {tool.name} designed for {industry} professionals. Industry-specific features, templates, and examples.',
                'seo_intro': f'{tool.name} for {industry.title()} Industry provides specialized functionality tailored to the unique needs of {industry} professionals. Our tool includes industry-specific templates, compliance features, and examples that address common {industry} challenges and workflows.',
                'use_cases': self._generate_industry_use_cases(tool, industry),
                'faq_items': self._generate_industry_faq_items(tool, industry),
                'keywords': [tool.name.lower(), industry, 'professional', 'industry', 'business'],
                'industry_features': self._get_industry_features(tool, industry),
                'compliance_notes': self._get_compliance_notes(tool, industry)
            }
            industry_pages.append(industry_page)
        
        return industry_pages
    
    def _generate_meta_title(self, tool: Tool, content_data: Dict[str, Any]) -> str:
        """Generate SEO-optimized meta title"""
        
        content_type = content_data.get('type', 'example')
        title = content_data.get('title', f'{tool.name} Example')
        
        patterns = [
            f'Free {title} - {tool.name} | LamGen',
            f'{title} - Free Online {tool.name} | LamGen',
            f'Generate {title} with {tool.name} | Free Tool | LamGen',
            f'{tool.name}: {title} | Free Online Generator | LamGen'
        ]
        
        # Choose best pattern based on content type
        if content_type in ['resume', 'bio', 'prompt']:
            return patterns[0]
        elif content_type in ['template', 'guide']:
            return patterns[1]
        else:
            return patterns[2]
    
    def _generate_meta_description(self, tool: Tool, content_data: Dict[str, Any]) -> str:
        """Generate SEO-optimized meta description"""
        
        content_type = content_data.get('type', 'example')
        title = content_data.get('title', 'Example')
        
        base_desc = f'Generate professional {title.lower()} using {tool.name}. '
        
        if content_type == 'resume':
            base_desc += 'ATS-friendly resume builder with professional templates and examples. '
        elif content_type == 'bio':
            base_desc += 'Professional bio generator with multiple styles and tones. '
        elif content_type == 'prompt':
            base_desc += 'AI prompt creator for better results and quality. '
        else:
            base_desc += 'Free online tool with instant results and examples. '
        
        base_desc += 'No signup required, 100% private.'
        
        return base_desc[:160]
    
    def _generate_seo_intro(self, tool: Tool, content_data: Dict[str, Any]) -> str:
        """Generate SEO-optimized introduction"""
        
        content_type = content_data.get('type', 'example')
        title = content_data.get('title', 'Example')
        
        intro = f'{title} created with {tool.name} demonstrates the power and versatility of our free online tool. '
        
        if content_type == 'resume':
            intro += 'This professional resume example showcases modern formatting, keyword optimization, and ATS-compliant structure that helps job seekers stand out in competitive markets. '
        elif content_type == 'bio':
            intro += 'This professional bio example illustrates how to create compelling personal narratives that work across different platforms and purposes, from LinkedIn profiles to company websites. '
        else:
            intro += 'This example provides a practical demonstration of the tool capabilities and serves as a starting point for users looking to achieve similar results. '
        
        intro += f'All processing happens locally in your browser, ensuring complete privacy and security. No account required, no data stored, and instant results available.'
        
        return intro
    
    def _generate_use_cases(self, tool: Tool, content_data: Dict[str, Any]) -> List[str]:
        """Generate relevant use cases"""
        
        content_type = content_data.get('type', 'example')
        
        base_use_cases = [
            f'Professionals creating {content_type} for career advancement',
            f'Students and educators using {content_type} for learning',
            f'Freelancers and consultants generating {content_type} for clients',
            f'Business professionals using {content_type} for documentation',
            f'Content creators incorporating {content_type} in their work'
        ]
        
        if content_type == 'resume':
            base_use_cases.extend([
                'Job seekers optimizing resumes for ATS systems',
                'Career changers highlighting transferable skills',
                'Recent graduates creating first professional resumes',
                'Executives developing executive-level summaries'
            ])
        elif content_type == 'bio':
            base_use_cases.extend([
                'LinkedIn profile optimization and networking',
                'Company website team pages and about sections',
                'Conference speaker bios and professional introductions',
                'Social media profile enhancement'
            ])
        
        return base_use_cases[:6]
    
    def _generate_faq_items(self, tool: Tool, content_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate FAQ items"""
        
        content_type = content_data.get('type', 'example')
        
        faqs = [
            {
                'q': f'Is this {content_type} free to use?',
                'a': f'Yes, this {content_type} and the {tool.name} tool are completely free with no hidden costs or premium features.'
            },
            {
                'q': f'Can I customize this {content_type}?',
                'a': f'Absolutely. Our {tool.name} tool allows full customization of the {content_type} to match your specific needs and preferences.'
            },
            {
                'q': f'Is my data secure when creating {content_type}?',
                'a': f'Yes, all {content_type} generation happens locally in your browser. No data is sent to servers or stored anywhere.'
            }
        ]
        
        if content_type == 'resume':
            faqs.extend([
                {
                    'q': 'Is this resume ATS-friendly?',
                    'a': 'Yes, all resume examples and templates are designed to pass Applicant Tracking Systems with proper formatting and keyword optimization.'
                },
                {
                    'q': 'Can I download in different formats?',
                    'a': 'Yes, you can download your resume in multiple formats including PDF, Word, and plain text for maximum compatibility.'
                }
            ])
        
        return faqs
    
    def _extract_keywords(self, tool: Tool, content_data: Dict[str, Any]) -> List[str]:
        """Extract relevant keywords"""
        
        base_keywords = [
            tool.name.lower(),
            'free', 'online', 'generator', 'creator', 'tool'
        ]
        
        content_type = content_data.get('type', 'example')
        type_keywords = {
            'resume': ['resume', 'cv', 'curriculum vitae', 'job application', 'career'],
            'bio': ['bio', 'biography', 'profile', 'about', 'introduction'],
            'prompt': ['prompt', 'ai prompt', 'chatgpt', 'instruction', 'query'],
            'template': ['template', 'format', 'structure', 'layout', 'framework'],
            'example': ['example', 'sample', 'demo', 'illustration', 'instance']
        }
        
        keywords = base_keywords + type_keywords.get(content_type, [])
        
        # Add category-specific keywords
        if tool.category:
            keywords.extend(tool.category.name.lower().split())
        
        return list(set(keywords))  # Remove duplicates
    
    def _calculate_quality_score(self, content_data: Dict[str, Any]) -> float:
        """Calculate content quality score (0.0 to 1.0)"""
        
        score = 0.0
        content = content_data.get('content', '')
        
        # Word count score (30%)
        word_count = len(content.split())
        if word_count >= 100:
            score += 0.3
        elif word_count >= 50:
            score += 0.2
        elif word_count >= 25:
            score += 0.1
        
        # Structure score (25%)
        if '\n' in content:  # Has structure
            score += 0.15
        if any(marker in content.lower() for marker in ['step', 'guide', 'instruction']):
            score += 0.1
        
        # Uniqueness score (25%)
        # Simplified uniqueness check
        unique_words = len(set(content.lower().split()))
        total_words = len(content.split())
        if total_words > 0:
            uniqueness_ratio = unique_words / total_words
            score += uniqueness_ratio * 0.25
        
        # Completeness score (20%)
        if content_data.get('title') and len(content_data.get('title', '')) > 5:
            score += 0.1
        if content_data.get('type'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _should_index(self, content_data: Dict[str, Any]) -> bool:
        """Determine if content should be indexed"""
        
        content = content_data.get('content', '')
        
        # Minimum requirements
        if len(content) < 25:
            return False
        
        # Quality threshold
        quality_score = self._calculate_quality_score(content_data)
        if quality_score < 0.3:
            return False
        
        # Content type restrictions
        restricted_types = ['test', 'demo', 'private']
        content_type = content_data.get('type', '')
        if content_type.lower() in restricted_types:
            return False
        
        return True
    
    def _generate_category_use_cases(self, tool: Tool, content_type: str) -> List[str]:
        """Generate category-specific use cases"""
        
        base_cases = {
            'resume': [
                'Job seekers creating professional resumes for applications',
                'Career changers highlighting transferable skills',
                'Students building first resumes for internships',
                'Professionals updating resumes for advancement'
            ],
            'bio': [
                'LinkedIn profile optimization and networking',
                'Company website team pages and bios',
                'Conference speaker profiles and introductions',
                'Social media professional profiles'
            ],
            'prompt': [
                'AI enthusiasts testing different prompt strategies',
                'Content creators improving AI-generated content',
                'Marketers optimizing prompts for campaigns',
                'Writers overcoming creative blocks with AI'
            ]
        }
        
        return base_cases.get(content_type, [
            f'Users creating {content_type} with {tool.name}',
            f'Professionals using {content_type} for work',
            f'Students learning with {content_type} examples'
        ])
    
    def _generate_category_faq_items(self, tool: Tool, content_type: str) -> List[Dict[str, str]]:
        """Generate category-specific FAQ items"""
        
        base_faqs = {
            'resume': [
                {
                    'q': 'What resume templates are available?',
                    'a': f'Our {tool.name} offers multiple resume templates including professional, modern, creative, and ATS-optimized formats for different industries and experience levels.'
                },
                {
                    'q': 'Can I edit my resume after generating?',
                    'a': 'Yes, you can edit and customize every section of your resume. Our tool provides full control over formatting, content, and structure.'
                }
            ],
            'bio': [
                {
                    'q': 'What bio styles can I generate?',
                    'a': f'Our {tool.name} creates various bio styles including professional, casual, creative, and narrative formats suitable for different platforms and purposes.'
                },
                {
                    'q': 'How long should a professional bio be?',
                    'a': 'Professional bios typically range from 50-300 words depending on the platform. Our tool helps you create appropriately sized bios for LinkedIn, websites, and other platforms.'
                }
            ]
        }
        
        return base_faqs.get(content_type, [
            {
                'q': f'Is {tool.name} really free?',
                'a': f'Yes, {tool.name} is completely free with no hidden costs, premium features, or usage limits.'
            }
        ])
    
    def _get_featured_examples(self, tool: Tool, content_type: str) -> List[Dict[str, Any]]:
        """Get featured examples for content type"""
        
        # This would typically pull from a database of examples
        # For now, return placeholder data
        return [
            {
                'title': f'Professional {content_type.title()} Example',
                'description': f'A high-quality {content_type} created with {tool.name}',
                'preview': f'Example of {content_type} generated using our tool'
            }
        ]
    
    def _count_available_templates(self, tool: Tool, content_type: str) -> int:
        """Count available templates"""
        
        # This would typically query a database
        # Return placeholder counts
        template_counts = {
            'resume': 12,
            'bio': 8,
            'prompt': 15,
            'template': 20,
            'example': 10
        }
        
        return template_counts.get(content_type, 5)
    
    def _generate_industry_use_cases(self, tool: Tool, industry: str) -> List[str]:
        """Generate industry-specific use cases"""
        
        industry_use_cases = {
            'healthcare': [
                'Medical professionals creating patient documentation',
                'Healthcare administrators developing reports',
                'Medical researchers formatting research papers',
                'Hospital staff creating training materials'
            ],
            'finance': [
                'Financial analysts creating reports and presentations',
                'Banking professionals developing compliance documents',
                'Investment managers preparing client communications',
                'Accounting teams generating financial statements'
            ],
            'technology': [
                'Software developers documenting projects',
                'IT professionals creating technical specifications',
                'DevOps teams generating deployment guides',
                'Tech support creating knowledge base articles'
            ]
        }
        
        return industry_use_cases.get(industry, [
            f'{industry.title()} professionals using {tool.name}',
            f'Business applications in {industry} sector',
            f'Industry-specific {tool.name} workflows'
        ])
    
    def _generate_industry_faq_items(self, tool: Tool, industry: str) -> List[Dict[str, str]]:
        """Generate industry-specific FAQ items"""
        
        return [
            {
                'q': f'Is {tool.name} suitable for {industry} industry?',
                'a': f'Yes, {tool.name} is designed to meet the specific needs of {industry} professionals with industry-specific features and compliance considerations.'
            },
            {
                'q': f'What {industry} compliance features are included?',
                'a': f'Our {tool.name} includes {industry}-specific compliance features, security measures, and best practices to ensure professional use.'
            }
        ]
    
    def _get_industry_features(self, tool: Tool, industry: str) -> List[str]:
        """Get industry-specific features"""
        
        feature_map = {
            'healthcare': ['HIPAA compliance', 'Patient privacy', 'Medical terminology'],
            'finance': ['SEC compliance', 'Financial formatting', 'Audit trails'],
            'technology': ['Code snippets', 'Technical documentation', 'API integration'],
            'legal': ['Legal formatting', 'Case law references', 'Citation styles']
        }
        
        return feature_map.get(industry, [f'{industry.title()} features', 'Professional templates'])
    
    def _get_compliance_notes(self, tool: Tool, industry: str) -> str:
        """Get compliance information"""
        
        compliance_map = {
            'healthcare': 'All healthcare content generation follows HIPAA guidelines and patient privacy standards.',
            'finance': 'Financial content tools include compliance features for SEC regulations and financial reporting standards.',
            'legal': 'Legal content tools support bar association guidelines and legal document formatting requirements.'
        }
        
        return compliance_map.get(industry, f'Professional {industry} standards and best practices are applied.')


# Singleton instance
user_content_indexer = UserContentIndexer()
