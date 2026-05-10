"""
SEO Validation and QA Automation
Comprehensive SEO validation system for quality assurance
"""

from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Q
from django.core.cache import cache
from django.urls import reverse
from tools.models import Tool, ToolCategory
from seo.models import SEOPage, LongTailVariant
import requests
import re
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class SEOValidator:
    """Comprehensive SEO validation and QA automation"""
    
    def __init__(self):
        self.cache_timeout = 60 * 30  # 30 minutes
        self.validation_thresholds = {
            'min_content_length': 300,
            'max_title_length': 60,
            'max_description_length': 160,
            'min_internal_links': 8,
            'max_internal_links': 20,
            'min_seo_score': 0.7,
            'max_response_time': 1.5,  # seconds
            'min_lighthouse_score': 85,
            'max_page_size': 100 * 1024,  # 100KB
        }
        
    def validate_tool_page(self, tool: Tool) -> Dict[str, Any]:
        """Comprehensive validation for tool pages"""
        
        validation_results = {
            'tool': tool,
            'timestamp': time.time(),
            'overall_score': 0.0,
            'issues': [],
            'warnings': [],
            'recommendations': [],
            'metrics': {}
        }
        
        # 1. Content Validation
        content_validation = self._validate_content(tool)
        validation_results['metrics']['content'] = content_validation
        
        # 2. SEO Elements Validation
        seo_validation = self._validate_seo_elements(tool)
        validation_results['metrics']['seo'] = seo_validation
        
        # 3. Technical SEO Validation
        technical_validation = self._validate_technical_seo(tool)
        validation_results['metrics']['technical'] = technical_validation
        
        # 4. Performance Validation
        performance_validation = self._validate_performance(tool)
        validation_results['metrics']['performance'] = performance_validation
        
        # 5. Schema Validation
        schema_validation = self._validate_structured_data(tool)
        validation_results['metrics']['schema'] = schema_validation
        
        # 6. Internal Links Validation
        links_validation = self._validate_internal_links(tool)
        validation_results['metrics']['links'] = links_validation
        
        # Calculate overall score
        validation_results['overall_score'] = self._calculate_overall_score(validation_results['metrics'])
        
        # Generate recommendations
        validation_results['recommendations'] = self._generate_recommendations(validation_results)
        
        # Classify issues
        validation_results['issues'] = self._classify_issues(validation_results)
        validation_results['warnings'] = self._classify_warnings(validation_results)
        
        return validation_results
    
    def validate_longtail_page(self, variant: LongTailVariant) -> Dict[str, Any]:
        """Validate long-tail SEO pages"""
        
        validation_results = {
            'variant': variant,
            'timestamp': time.time(),
            'overall_score': 0.0,
            'issues': [],
            'warnings': [],
            'recommendations': [],
            'metrics': {}
        }
        
        # Content uniqueness validation
        uniqueness_score = self._validate_content_uniqueness(variant)
        validation_results['metrics']['uniqueness'] = uniqueness_score
        
        # Keyword optimization validation
        keyword_validation = self._validate_keyword_optimization(variant)
        validation_results['metrics']['keywords'] = keyword_validation
        
        # Intent alignment validation
        intent_validation = self._validate_intent_alignment(variant)
        validation_results['metrics']['intent'] = intent_validation
        
        # Canonical URL validation
        canonical_validation = self._validate_canonical_url(variant)
        validation_results['metrics']['canonical'] = canonical_validation
        
        # Calculate overall score
        validation_results['overall_score'] = self._calculate_longtail_score(validation_results['metrics'])
        
        # Generate recommendations
        validation_results['recommendations'] = self._generate_longtail_recommendations(validation_results)
        
        return validation_results
    
    def validate_category_page(self, category: ToolCategory) -> Dict[str, Any]:
        """Validate category pages"""
        
        validation_results = {
            'category': category,
            'timestamp': time.time(),
            'overall_score': 0.0,
            'issues': [],
            'warnings': [],
            'recommendations': [],
            'metrics': {}
        }
        
        # Category authority validation
        authority_validation = self._validate_category_authority(category)
        validation_results['metrics']['authority'] = authority_validation
        
        # Internal linking validation
        category_links_validation = self._validate_category_links(category)
        validation_results['metrics']['category_links'] = category_links_validation
        
        # Content depth validation
        depth_validation = self._validate_content_depth(category)
        validation_results['metrics']['depth'] = depth_validation
        
        # Calculate overall score
        validation_results['overall_score'] = self._calculate_category_score(validation_results['metrics'])
        
        return validation_results
    
    def _validate_content(self, tool: Tool) -> Dict[str, Any]:
        """Validate content quality and quantity"""
        
        validation = {
            'score': 0.0,
            'issues': [],
            'metrics': {}
        }
        
        # Content length validation
        intro_length = len(tool.seo_intro or '')
        use_cases_length = len(tool.use_cases or '')
        total_length = intro_length + use_cases_length
        
        if total_length < self.validation_thresholds['min_content_length']:
            validation['issues'].append({
                'type': 'content_too_short',
                'severity': 'high',
                'message': f'Content is too short ({total_length} words). Minimum {self.validation_thresholds["min_content_length"]} words required.'
            })
        elif total_length < self.validation_thresholds['min_content_length'] * 2:
            validation['issues'].append({
                'type': 'content_short',
                'severity': 'medium',
                'message': f'Content could be longer ({total_length} words). Target {self.validation_thresholds["min_content_length"] * 2}+ words.'
            })
        
        # Content uniqueness validation
        uniqueness_score = self._calculate_uniqueness_score(tool)
        validation['metrics']['uniqueness'] = uniqueness_score
        
        if uniqueness_score < 0.8:
            validation['issues'].append({
                'type': 'duplicate_content',
                'severity': 'medium',
                'message': f'Content uniqueness score is low ({uniqueness_score:.2f}). Aim for 0.8+.'
            })
        
        # FAQ validation
        faq_validation = self._validate_faqs(tool)
        validation['metrics']['faq'] = faq_validation
        
        # Examples validation
        examples_validation = self._validate_examples(tool)
        validation['metrics']['examples'] = examples_validation
        
        # Calculate content score
        validation['score'] = self._calculate_content_score(validation['metrics'])
        
        return validation
    
    def _validate_seo_elements(self, tool: Tool) -> Dict[str, Any]:
        """Validate SEO meta elements"""
        
        validation = {
            'score': 0.0,
            'issues': [],
            'metrics': {}
        }
        
        # Title validation
        title = tool.meta_title or ''
        title_length = len(title)
        
        if title_length == 0:
            validation['issues'].append({
                'type': 'missing_title',
                'severity': 'critical',
                'message': 'Meta title is missing.'
            })
        elif title_length > self.validation_thresholds['max_title_length']:
            validation['issues'].append({
                'type': 'title_too_long',
                'severity': 'medium',
                'message': f'Title is too long ({title_length} chars). Maximum {self.validation_thresholds["max_title_length"]} characters.'
            })
        elif not any(keyword.lower() in title.lower() for keyword in tool.get_all_keywords()):
            validation['issues'].append({
                'type': 'title_missing_keywords',
                'severity': 'medium',
                'message': 'Title should include primary keywords.'
            })
        
        validation['metrics']['title_length'] = title_length
        validation['metrics']['title_has_keywords'] = any(keyword.lower() in title.lower() for keyword in tool.get_all_keywords())
        
        # Description validation
        description = tool.meta_description or ''
        description_length = len(description)
        
        if description_length == 0:
            validation['issues'].append({
                'type': 'missing_description',
                'severity': 'critical',
                'message': 'Meta description is missing.'
            })
        elif description_length > self.validation_thresholds['max_description_length']:
            validation['issues'].append({
                'type': 'description_too_long',
                'severity': 'medium',
                'message': f'Description is too long ({description_length} chars). Maximum {self.validation_thresholds["max_description_length"]} characters.'
            })
        elif not any(keyword.lower() in description.lower() for keyword in tool.get_all_keywords()):
            validation['issues'].append({
                'type': 'description_missing_keywords',
                'severity': 'medium',
                'message': 'Description should include primary keywords.'
            })
        
        validation['metrics']['description_length'] = description_length
        validation['metrics']['description_has_keywords'] = any(keyword.lower() in description.lower() for keyword in tool.get_all_keywords())
        
        # H1 validation
        h1_validation = self._validate_h1(tool)
        validation['metrics']['h1'] = h1_validation
        
        # Calculate SEO elements score
        validation['score'] = self._calculate_seo_elements_score(validation['metrics'])
        
        return validation
    
    def _validate_technical_seo(self, tool: Tool) -> Dict[str, Any]:
        """Validate technical SEO elements"""
        
        validation = {
            'score': 0.0,
            'issues': [],
            'metrics': {}
        }
        
        # Canonical URL validation
        canonical = tool.canonical_url or ''
        if not canonical:
            validation['issues'].append({
                'type': 'missing_canonical',
                'severity': 'high',
                'message': 'Canonical URL is missing.'
            })
        elif not canonical.startswith('http'):
            validation['issues'].append({
                'type': 'invalid_canonical',
                'severity': 'medium',
                'message': 'Canonical URL should be absolute.'
            })
        
        validation['metrics']['has_canonical'] = bool(canonical)
        
        # Robots.txt validation
        robots_validation = self._validate_robots_txt()
        validation['metrics']['robots'] = robots_validation
        
        # Sitemap validation
        sitemap_validation = self._validate_sitemap()
        validation['metrics']['sitemap'] = sitemap_validation
        
        # Schema validation
        schema_validation = self._validate_schema_markup(tool)
        validation['metrics']['schema_markup'] = schema_validation
        
        # Calculate technical SEO score
        validation['score'] = self._calculate_technical_seo_score(validation['metrics'])
        
        return validation
    
    def _validate_performance(self, tool: Tool) -> Dict[str, Any]:
        """Validate page performance"""
        
        validation = {
            'score': 0.0,
            'issues': [],
            'metrics': {}
        }
        
        # Page load time validation
        start_time = time.time()
        try:
            response = requests.get(
                f"https://lamgen.com{tool.get_absolute_url()}",
                timeout=10,
                headers={'User-Agent': 'LamGen-SEO-Validator/1.0'}
            )
            load_time = time.time() - start_time
            
            if load_time > self.validation_thresholds['max_response_time']:
                validation['issues'].append({
                    'type': 'slow_page',
                    'severity': 'high',
                    'message': f'Page load time is {load_time:.2f}s. Target <{self.validation_thresholds["max_response_time"]}s.'
                })
            
            validation['metrics']['load_time'] = load_time
            validation['metrics']['status_code'] = response.status_code
            
        except Exception as e:
            validation['issues'].append({
                'type': 'page_unreachable',
                'severity': 'critical',
                'message': f'Page is unreachable: {str(e)}'
            })
            validation['metrics']['load_time'] = None
            validation['metrics']['status_code'] = None
        
        # Page size validation
        # This would be measured from actual response
        validation['metrics']['page_size'] = 'unknown'  # Would be measured in middleware
        
        # Calculate performance score
        validation['score'] = self._calculate_performance_score(validation['metrics'])
        
        return validation
    
    def _validate_structured_data(self, tool: Tool) -> Dict[str, Any]:
        """Validate structured data (JSON-LD)"""
        
        validation = {
            'score': 0.0,
            'issues': [],
            'metrics': {}
        }
        
        # Check for required schemas
        required_schemas = ['SoftwareApplication', 'FAQPage', 'BreadcrumbList']
        found_schemas = []
        
        # This would validate actual schema markup in rendered page
        # For now, check if tool has schema_type set
        if tool.schema_type:
            found_schemas.append(tool.schema_type)
        
        missing_schemas = set(required_schemas) - set(found_schemas)
        if missing_schemas:
            validation['issues'].append({
                'type': 'missing_schemas',
                'severity': 'medium',
                'message': f'Missing required schemas: {", ".join(missing_schemas)}'
            })
        
        validation['metrics']['found_schemas'] = found_schemas
        validation['metrics']['missing_schemas'] = list(missing_schemas)
        
        # Calculate schema score
        validation['score'] = self._calculate_schema_score(validation['metrics'])
        
        return validation
    
    def _validate_internal_links(self, tool: Tool) -> Dict[str, Any]:
        """Validate internal linking"""
        
        validation = {
            'score': 0.0,
            'issues': [],
            'metrics': {}
        }
        
        # Get internal links (would be from actual page analysis)
        # For now, simulate link count based on related tools
        related_tools_count = tool.get_related_tools_by_keywords(
            Tool.objects.filter(category=tool.category, is_active=True),
            limit=20
        ).count()
        
        if related_tools_count < self.validation_thresholds['min_internal_links']:
            validation['issues'].append({
                'type': 'insufficient_internal_links',
                'severity': 'medium',
                'message': f'Too few internal links ({related_tools_count}). Minimum {self.validation_thresholds["min_internal_links"]} required.'
            })
        elif related_tools_count > self.validation_thresholds['max_internal_links']:
            validation['issues'].append({
                'type': 'too_many_internal_links',
                'severity': 'low',
                'message': f'Too many internal links ({related_tools_count}). Maximum {self.validation_thresholds["max_internal_links"]} recommended.'
            })
        
        validation['metrics']['internal_links_count'] = related_tools_count
        
        # Calculate links score
        validation['score'] = self._calculate_links_score(validation['metrics'])
        
        return validation
    
    def _calculate_overall_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall SEO score"""
        
        scores = []
        
        # Content score (30%)
        if 'content' in metrics:
            scores.append(metrics['content'].get('score', 0) * 0.3)
        
        # SEO elements score (25%)
        if 'seo' in metrics:
            scores.append(metrics['seo'].get('score', 0) * 0.25)
        
        # Technical SEO score (20%)
        if 'technical' in metrics:
            scores.append(metrics['technical'].get('score', 0) * 0.2)
        
        # Performance score (15%)
        if 'performance' in metrics:
            scores.append(metrics['performance'].get('score', 0) * 0.15)
        
        # Schema score (10%)
        if 'schema' in metrics:
            scores.append(metrics['schema'].get('score', 0) * 0.1)
        
        return min(sum(scores), 1.0)
    
    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Content recommendations
        if 'content' in validation_results['metrics']:
            content_metrics = validation_results['metrics']['content']
            if content_metrics.get('score', 0) < 0.8:
                recommendations.append("Expand content to at least 1200 words with more detailed explanations and examples")
            
            if content_metrics.get('uniqueness', 0) < 0.8:
                recommendations.append("Improve content uniqueness by adding unique insights and original examples")
        
        # SEO recommendations
        if 'seo' in validation_results['metrics']:
            seo_metrics = validation_results['metrics']['seo']
            if not seo_metrics.get('title_has_keywords', False):
                recommendations.append("Add primary keywords to meta title for better ranking")
            
            if not seo_metrics.get('description_has_keywords', False):
                recommendations.append("Include primary keywords in meta description for improved CTR")
        
        # Technical SEO recommendations
        if 'technical' in validation_results['metrics']:
            tech_metrics = validation_results['metrics']['technical']
            if not tech_metrics.get('has_canonical', False):
                recommendations.append("Add canonical URL to prevent duplicate content issues")
            
            if tech_metrics.get('missing_schemas'):
                recommendations.append("Implement required JSON-LD schemas for better search engine understanding")
        
        # Performance recommendations
        if 'performance' in validation_results['metrics']:
            perf_metrics = validation_results['metrics']['performance']
            if perf_metrics.get('load_time', 0) > self.validation_thresholds['max_response_time']:
                recommendations.append("Optimize page load time to under 1.5 seconds for better user experience")
        
        # Links recommendations
        if 'links' in validation_results['metrics']:
            links_metrics = validation_results['metrics']['links']
            if links_metrics.get('internal_links_count', 0) < self.validation_thresholds['min_internal_links']:
                recommendations.append("Add more relevant internal links to improve page authority and user navigation")
        
        return recommendations
    
    def _classify_issues(self, validation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Classify issues by severity"""
        
        all_issues = []
        
        for metric_type, metric_data in validation_results['metrics'].items():
            if 'issues' in metric_data:
                all_issues.extend(metric_data['issues'])
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_issues.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        return all_issues
    
    def _classify_warnings(self, validation_results: Dict[str, Any]) -> List[str]:
        """Classify warnings"""
        
        warnings = []
        
        # Add warnings based on scores
        for metric_type, metric_data in validation_results['metrics'].items():
            score = metric_data.get('score', 1.0)
            if 0.6 <= score < 0.8:
                warnings.append(f"{metric_type.title()} score needs improvement")
        
        return warnings
    
    def run_batch_validation(self, limit: int = 50) -> Dict[str, Any]:
        """Run validation on multiple tools/pages"""
        
        batch_results = {
            'timestamp': time.time(),
            'total_validated': 0,
            'average_score': 0.0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
            'results': []
        }
        
        # Get tools to validate
        tools = Tool.objects.filter(is_active=True).select_related('category')[:limit]
        
        total_score = 0.0
        issue_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for tool in tools:
            validation_result = self.validate_tool_page(tool)
            batch_results['results'].append(validation_result)
            
            total_score += validation_result['overall_score']
            
            # Count issues by severity
            for issue in validation_result['issues']:
                severity = issue.get('severity', 'low')
                if severity in issue_counts:
                    issue_counts[severity] += 1
        
        batch_results['total_validated'] = len(tools)
        batch_results['average_score'] = total_score / len(tools) if tools else 0.0
        batch_results['critical_issues'] = issue_counts['critical']
        batch_results['high_issues'] = issue_counts['high']
        batch_results['medium_issues'] = issue_counts['medium']
        batch_results['low_issues'] = issue_counts['low']
        
        return batch_results
    
    def generate_qa_report(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive QA report"""
        
        report = {
            'generated_at': time.time(),
            'total_pages': len(validation_results),
            'summary': {
                'average_score': 0.0,
                'critical_issues': 0,
                'high_issues': 0,
                'medium_issues': 0,
                'low_issues': 0,
                'pages_above_threshold': 0,
                'pages_below_threshold': 0
            },
            'recommendations': [],
            'top_issues': [],
            'priority_actions': []
        }
        
        if not validation_results:
            return report
        
        total_score = sum(result['overall_score'] for result in validation_results)
        report['summary']['average_score'] = total_score / len(validation_results)
        
        # Count issues
        issue_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for result in validation_results:
            for issue in result['issues']:
                severity = issue.get('severity', 'low')
                if severity in issue_counts:
                    issue_counts[severity] += 1
            
            if result['overall_score'] >= self.validation_thresholds['min_seo_score']:
                report['summary']['pages_above_threshold'] += 1
            else:
                report['summary']['pages_below_threshold'] += 1
        
        report['summary']['critical_issues'] = issue_counts['critical']
        report['summary']['high_issues'] = issue_counts['high']
        report['summary']['medium_issues'] = issue_counts['medium']
        report['summary']['low_issues'] = issue_counts['low']
        
        # Generate top recommendations
        all_recommendations = []
        for result in validation_results:
            all_recommendations.extend(result.get('recommendations', []))
        
        # Count recommendation frequency
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        # Get top recommendations
        report['recommendations'] = sorted(
            recommendation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Generate priority actions
        report['priority_actions'] = [
            "Fix all critical and high severity issues immediately",
            "Improve pages with scores below 0.7",
            "Add missing SEO elements (titles, descriptions, canonical URLs)",
            "Optimize page load times above 1.5 seconds",
            "Ensure minimum 8 internal links per page",
            "Implement required JSON-LD schemas"
        ]
        
        return report


# Singleton instance
seo_validator = SEOValidator()
