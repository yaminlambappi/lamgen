"""
Smart Indexing Strategy System
Implements noindex rules to only index pages with real utility
"""

from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, Count, F, Avg
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from apps.tools.models import Tool, ToolCategory
from apps.seo.models import SEOPage, LongTailVariant
import json
import time
from datetime import datetime, timedelta
import random


class SmartIndexingStrategy:
    """Smart indexing strategy with noindex rules"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 12  # 12 hours
        
        # Indexing rules and thresholds
        self.indexing_rules = {
            "min_word_count": 300,              # Minimum word count for indexing
            "min_internal_links": 8,           # Minimum internal links
            "min_seo_score": 70,               # Minimum SEO quality score
            "min_uniqueness_score": 0.8,        # Minimum uniqueness score
            "min_content_depth": 0.6,          # Minimum content depth
            "max_duplicate_intent": 0.1,       # Maximum duplicate intent
            "min_user_signals": 5,              # Minimum user signals
            "min_age_days": 7,                  # Minimum age before indexing
            "max_orphan_pages": 0.05            # Maximum orphan pages ratio
        }
        
        # Noindex criteria
        self.noindex_criteria = {
            "low_value_variants": {
                "description": "Low-value longtail variants",
                "conditions": {
                    "word_count": {"operator": "<", "value": 200},
                    "uniqueness_score": {"operator": "<", "value": 0.7},
                    "user_signals": {"operator": "<", "value": 3}
                }
            },
            "duplicate_intent_pages": {
                "description": "Pages with duplicate intent",
                "conditions": {
                    "duplicate_intent_score": {"operator": ">", "value": 0.15}
                }
            },
            "weak_generated_outputs": {
                "description": "Weak tool outputs",
                "conditions": {
                    "content_quality": {"operator": "<", "value": 0.6},
                    "word_count": {"operator": "<", "value": 150},
                    "examples_count": {"operator": "<", "value": 1}
                }
            },
            "empty_states": {
                "description": "Empty or placeholder pages",
                "conditions": {
                    "has_content": {"operator": "=", "value": False},
                    "word_count": {"operator": "<", "value": 50}
                }
            },
            "test_pages": {
                "description": "Test and development pages",
                "conditions": {
                    "is_test": {"operator": "=", "value": True},
                    "environment": {"operator": "=", "value": "development"}
                }
            }
        }
        
        # Priority indexing criteria
        self.priority_indexing = {
            "high_priority": {
                "description": "High-value pages to index immediately",
                "conditions": {
                    "content_quality": {"operator": ">=", "value": 0.9},
                    "word_count": {"operator": ">=", "value": 1000},
                    "user_signals": {"operator": ">=", "value": 10},
                    "authority_score": {"operator": ">=", "value": 80}
                }
            },
            "medium_priority": {
                "description": "Medium-value pages to index",
                "conditions": {
                    "content_quality": {"operator": ">=", "value": 0.7},
                    "word_count": {"operator": ">=", "value": 500},
                    "user_signals": {"operator": ">=", "value": 5},
                    "authority_score": {"operator": ">=", "value": 60}
                }
            }
        }
    
    def evaluate_indexing_strategy(self) -> Dict[str, Any]:
        """Evaluate and implement smart indexing strategy"""
        
        evaluation_report = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "total_pages": 0,
            "indexable_pages": 0,
            "noindex_pages": 0,
            "priority_pages": {},
            "noindex_analysis": {},
            "quality_metrics": {},
            "indexing_recommendations": [],
            "implementation_plan": {},
            "time_taken": 0
        }
        
        start_time = time.time()
        
        # Get all pages for evaluation
        all_pages = self._get_all_pages_for_evaluation()
        evaluation_report["total_pages"] = len(all_pages)
        
        # Evaluate each page
        page_evaluations = []
        for page in all_pages:
            evaluation = self._evaluate_page_indexing(page)
            page_evaluations.append(evaluation)
        
        # Categorize pages
        indexable_pages = [p for p in page_evaluations if p["should_index"]]
        noindex_pages = [p for p in page_evaluations if not p["should_index"]]
        
        evaluation_report["indexable_pages"] = len(indexable_pages)
        evaluation_report["noindex_pages"] = len(noindex_pages)
        
        # Analyze priority pages
        priority_pages = self._categorize_priority_pages(indexable_pages)
        evaluation_report["priority_pages"] = priority_pages
        
        # Analyze noindex reasons
        noindex_analysis = self._analyze_noindex_reasons(noindex_pages)
        evaluation_report["noindex_analysis"] = noindex_analysis
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(page_evaluations)
        evaluation_report["quality_metrics"] = quality_metrics
        
        # Generate recommendations
        recommendations = self._generate_indexing_recommendations(evaluation_report)
        evaluation_report["indexing_recommendations"] = recommendations
        
        # Create implementation plan
        implementation_plan = self._create_implementation_plan(evaluation_report)
        evaluation_report["implementation_plan"] = implementation_plan
        
        end_time = time.time()
        evaluation_report["time_taken"] = end_time - start_time
        
        # Cache results
        cache.set("smart_indexing_strategy", evaluation_report, self.cache_timeout)
        
        return evaluation_report
    
    def _get_all_pages_for_evaluation(self) -> List[Dict[str, Any]]:
        """Get all pages for indexing evaluation"""
        
        pages = []
        
        # Add tools
        tools = Tool.objects.filter(is_active=True).select_related('category')
        for tool in tools:
            pages.append({
                "type": "tool",
                "id": tool.id,
                "url": tool.get_absolute_url(),
                "title": tool.name,
                "slug": tool.slug,
                "category": tool.category.name if tool.category else None,
                "created_at": tool.created_at,
                "updated_at": tool.updated_at,
                "view_count": tool.view_count,
                "is_featured": tool.is_featured,
                "model": tool
            })
        
        # Add SEO pages
        seo_pages = SEOPage.objects.filter(is_active=True).select_related('category')
        for page in seo_pages:
            pages.append({
                "type": "seo_page",
                "id": page.id,
                "url": page.get_absolute_url(),
                "title": page.topic,
                "slug": page.slug,
                "category": page.category.name if page.category else None,
                "created_at": page.created_at,
                "updated_at": page.updated_at,
                "view_count": getattr(page, 'view_count', 0),
                "is_featured": getattr(page, 'is_featured', False),
                "model": page
            })
        
        # Add categories
        categories = ToolCategory.objects.filter(is_active=True)
        for category in categories:
            pages.append({
                "type": "category",
                "id": category.id,
                "url": category.get_absolute_url(),
                "title": category.name,
                "slug": category.slug,
                "category": category.name,
                "created_at": category.created_at,
                "updated_at": category.updated_at,
                "view_count": getattr(category, 'view_count', 0),
                "is_featured": getattr(category, 'is_featured', False),
                "model": category
            })
        
        # Add longtail variants
        longtails = LongTailVariant.objects.filter(is_active=True).select_related('tool')
        for variant in longtails:
            pages.append({
                "type": "longtail",
                "id": variant.id,
                "url": variant.get_absolute_url(),
                "title": variant.title,
                "slug": variant.slug,
                "category": variant.tool.category.name if variant.tool and variant.tool.category else None,
                "created_at": variant.created_at,
                "updated_at": variant.updated_at,
                "view_count": getattr(variant, 'view_count', 0),
                "is_featured": getattr(variant, 'is_featured', False),
                "model": variant
            })
        
        return pages
    
    def _evaluate_page_indexing(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if a page should be indexed"""
        
        evaluation = {
            "page_info": page,
            "should_index": False,
            "priority": "low",
            "noindex_reasons": [],
            "indexing_factors": {},
            "quality_score": 0.0,
            "recommendations": []
        }
        
        # Calculate indexing factors
        factors = self._calculate_indexing_factors(page)
        evaluation["indexing_factors"] = factors
        
        # Calculate quality score
        quality_score = self._calculate_page_quality_score(factors)
        evaluation["quality_score"] = quality_score
        
        # Check noindex criteria
        noindex_reasons = self._check_noindex_criteria(page, factors)
        evaluation["noindex_reasons"] = noindex_reasons
        
        # Check priority criteria
        priority = self._determine_page_priority(page, factors)
        evaluation["priority"] = priority
        
        # Make indexing decision
        if not noindex_reasons and quality_score >= self.indexing_rules["min_seo_score"]:
            evaluation["should_index"] = True
        
        # Generate recommendations
        evaluation["recommendations"] = self._generate_page_recommendations(page, factors, noindex_reasons)
        
        return evaluation
    
    def _calculate_indexing_factors(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate indexing factors for page"""
        
        factors = {
            "word_count": self._calculate_word_count(page),
            "internal_links": self._calculate_internal_links(page),
            "content_quality": self._assess_content_quality(page),
            "uniqueness_score": self._assess_uniqueness(page),
            "content_depth": self._assess_content_depth(page),
            "user_signals": self._assess_user_signals(page),
            "authority_score": self._calculate_authority_score(page),
            "duplicate_intent": self._assess_duplicate_intent(page),
            "page_age_days": self._calculate_page_age(page),
            "is_orphan": self._check_if_orphan(page),
            "has_content": self._check_has_content(page)
        }
        
        return factors
    
    def _calculate_word_count(self, page: Dict[str, Any]) -> int:
        """Calculate word count for page"""
        
        word_count = 0
        model = page["model"]
        
        if page["type"] == "tool":
            if model.seo_intro:
                word_count += len(model.seo_intro.split())
            if model.use_cases:
                word_count += sum(len(uc.split()) for uc in model.use_cases)
            if model.faq_items:
                for faq in model.faq_items:
                    if isinstance(faq, dict):
                        word_count += len(faq.get('q', '').split()) + len(faq.get('a', '').split())
            if model.examples:
                word_count += len(model.examples) * 50  # Estimate 50 words per example
        
        elif page["type"] == "seo_page":
            if model.content_intro:
                word_count += len(model.content_intro.split())
            if model.items:
                word_count += len(str(model.items).split())
        
        elif page["type"] == "category":
            if model.category_intro:
                word_count += len(model.category_intro.split())
            if model.best_use_cases:
                word_count += sum(len(uc.split()) for uc in model.best_use_cases)
        
        elif page["type"] == "longtail":
            if model.content:
                word_count += len(model.content.split())
        
        return max(word_count, 50)  # Minimum 50 words
    
    def _calculate_internal_links(self, page: Dict[str, Any]) -> int:
        """Calculate internal links for page"""
        
        # Simulate internal links count
        base_links = {
            "tool": 12,
            "seo_page": 15,
            "category": 20,
            "longtail": 8
        }
        
        base_count = base_links.get(page["type"], 10)
        
        # Add variation based on content quality
        content_quality = self._assess_content_quality(page)
        variation = int(base_count * content_quality)
        
        return base_count + variation
    
    def _assess_content_quality(self, page: Dict[str, Any]) -> float:
        """Assess content quality (0-1 scale)"""
        
        quality = 0.5  # Base quality
        
        model = page["model"]
        
        # Check for essential elements
        if page["type"] == "tool":
            if model.seo_intro:
                quality += 0.1
            if model.use_cases:
                quality += 0.1
            if model.faq_items:
                quality += 0.1
            if model.examples:
                quality += 0.1
            if model.meta_title and model.meta_description:
                quality += 0.1
        
        elif page["type"] == "seo_page":
            if model.content_intro:
                quality += 0.15
            if model.items:
                quality += 0.15
            if model.meta_title and model.meta_description:
                quality += 0.1
            if model.faq_items:
                quality += 0.1
        
        elif page["type"] == "category":
            if model.category_intro:
                quality += 0.2
            if model.best_use_cases:
                quality += 0.15
            if model.related_guides:
                quality += 0.1
            if model.category_faq:
                quality += 0.1
        
        elif page["type"] == "longtail":
            if model.content:
                quality += 0.3
            if model.meta_title and model.meta_description:
                quality += 0.2
        
        return min(quality, 1.0)
    
    def _assess_uniqueness(self, page: Dict[str, Any]) -> float:
        """Assess content uniqueness (0-1 scale)"""
        
        # Simulate uniqueness assessment
        base_uniqueness = {
            "tool": 0.85,
            "seo_page": 0.9,
            "category": 0.8,
            "longtail": 0.7
        }
        
        uniqueness = base_uniqueness.get(page["type"], 0.8)
        
        # Adjust based on content quality
        content_quality = self._assess_content_quality(page)
        uniqueness += (content_quality - 0.5) * 0.2  # Adjust by content quality
        
        return min(max(uniqueness, 0.0), 1.0)
    
    def _assess_content_depth(self, page: Dict[str, Any]) -> float:
        """Assess content depth (0-1 scale)"""
        
        depth = 0.3  # Base depth
        
        word_count = self._calculate_word_count(page)
        
        if word_count >= 1000:
            depth = 0.9
        elif word_count >= 500:
            depth = 0.7
        elif word_count >= 300:
            depth = 0.5
        elif word_count >= 150:
            depth = 0.3
        
        # Adjust for page type
        if page["type"] == "seo_page":
            depth += 0.1  # SEO pages get bonus
        elif page["type"] == "longtail":
            depth -= 0.1  # Longtail pages get penalty
        
        return min(max(depth, 0.0), 1.0)
    
    def _assess_user_signals(self, page: Dict[str, Any]) -> int:
        """Assess user signals"""
        
        # Simulate user signals based on view count and engagement
        view_count = page.get("view_count", 0)
        
        if view_count >= 1000:
            return 20
        elif view_count >= 500:
            return 15
        elif view_count >= 100:
            return 10
        elif view_count >= 50:
            return 5
        elif view_count >= 10:
            return 2
        else:
            return 0
    
    def _calculate_authority_score(self, page: Dict[str, Any]) -> float:
        """Calculate authority score"""
        
        base_authority = {
            "tool": 50,
            "seo_page": 70,
            "category": 80,
            "longtail": 30
        }
        
        authority = base_authority.get(page["type"], 50)
        
        # Adjust for featured status
        if page.get("is_featured"):
            authority += 20
        
        # Adjust for view count
        view_count = page.get("view_count", 0)
        if view_count >= 1000:
            authority += 15
        elif view_count >= 500:
            authority += 10
        elif view_count >= 100:
            authority += 5
        
        # Adjust for content quality
        content_quality = self._assess_content_quality(page)
        authority += content_quality * 20
        
        return min(authority, 100)
    
    def _assess_duplicate_intent(self, page: Dict[str, Any]) -> float:
        """Assess duplicate intent (0-1 scale)"""
        
        # Simulate duplicate intent assessment
        # Lower is better (less duplicate intent)
        
        duplicate_intent = 0.05  # Base duplicate intent
        
        # Increase for longtail pages (higher chance of duplicate intent)
        if page["type"] == "longtail":
            duplicate_intent += 0.1
        
        # Increase for pages with low content quality
        content_quality = self._assess_content_quality(page)
        if content_quality < 0.5:
            duplicate_intent += 0.15
        
        # Increase for pages with low uniqueness
        uniqueness = self._assess_uniqueness(page)
        if uniqueness < 0.7:
            duplicate_intent += 0.1
        
        return min(duplicate_intent, 1.0)
    
    def _calculate_page_age(self, page: Dict[str, Any]) -> int:
        """Calculate page age in days"""
        
        created_at = page.get("created_at", timezone.now())
        if created_at:
            return (timezone.now() - created_at).days
        else:
            return 30  # Default to 30 days if no creation date
    
    def _check_if_orphan(self, page: Dict[str, Any]) -> bool:
        """Check if page is orphan"""
        
        # Simulate orphan check
        # Randomly mark some pages as orphan for demonstration
        return random.random() < 0.05  # 5% chance of being orphan
    
    def _check_has_content(self, page: Dict[str, Any]) -> bool:
        """Check if page has content"""
        
        model = page["model"]
        
        if page["type"] == "tool":
            return bool(model.seo_intro or model.use_cases or model.faq_items)
        elif page["type"] == "seo_page":
            return bool(model.content_intro or model.items)
        elif page["type"] == "category":
            return bool(model.category_intro or model.best_use_cases)
        elif page["type"] == "longtail":
            return bool(getattr(model, 'content', None))
        
        return False
    
    def _check_noindex_criteria(self, page: Dict[str, Any], factors: Dict[str, Any]) -> List[str]:
        """Check if page meets noindex criteria"""
        
        noindex_reasons = []
        
        # Check low-value variants
        if page["type"] == "longtail":
            criteria = self.noindex_criteria["low_value_variants"]["conditions"]
            
            if factors["word_count"] < criteria["word_count"]["value"]:
                noindex_reasons.append(f"Low word count: {factors['word_count']} < {criteria['word_count']['value']}")
            
            if factors["uniqueness_score"] < criteria["uniqueness_score"]["value"]:
                noindex_reasons.append(f"Low uniqueness: {factors['uniqueness_score']:.2f} < {criteria['uniqueness_score']['value']}")
            
            if factors["user_signals"] < criteria["user_signals"]["value"]:
                noindex_reasons.append(f"Low user signals: {factors['user_signals']} < {criteria['user_signals']['value']}")
        
        # Check duplicate intent
        if factors["duplicate_intent"] > self.indexing_rules["max_duplicate_intent"]:
            noindex_reasons.append(f"High duplicate intent: {factors['duplicate_intent']:.2f} > {self.indexing_rules['max_duplicate_intent']}")
        
        # Check weak generated outputs
        if page["type"] in ["tool", "longtail"]:
            if factors["content_quality"] < 0.6:
                noindex_reasons.append(f"Weak content quality: {factors['content_quality']:.2f}")
            
            if factors["word_count"] < 150:
                noindex_reasons.append(f"Insufficient content: {factors['word_count']} words")
        
        # Check empty states
        if not factors["has_content"]:
            noindex_reasons.append("Empty or placeholder page")
        
        # Check page age
        if factors["page_age_days"] < self.indexing_rules["min_age_days"]:
            noindex_reasons.append(f"Page too new: {factors['page_age_days']} days old")
        
        # Check orphan status
        if factors["is_orphan"]:
            noindex_reasons.append("Orphan page with no internal links")
        
        return noindex_reasons
    
    def _determine_page_priority(self, page: Dict[str, Any], factors: Dict[str, Any]) -> str:
        """Determine page priority for indexing"""
        
        # Check high priority criteria
        high_criteria = self.priority_indexing["high_priority"]["conditions"]
        
        meets_high = True
        for factor, condition in high_criteria.items():
            if factor in factors:
                operator = condition["operator"]
                value = condition["value"]
                factor_value = factors[factor]
                
                if operator == ">=" and factor_value < value:
                    meets_high = False
                    break
                elif operator == ">" and factor_value <= value:
                    meets_high = False
                    break
        
        if meets_high:
            return "high"
        
        # Check medium priority criteria
        medium_criteria = self.priority_indexing["medium_priority"]["conditions"]
        
        meets_medium = True
        for factor, condition in medium_criteria.items():
            if factor in factors:
                operator = condition["operator"]
                value = condition["value"]
                factor_value = factors[factor]
                
                if operator == ">=" and factor_value < value:
                    meets_medium = False
                    break
                elif operator == ">" and factor_value <= value:
                    meets_medium = False
                    break
        
        if meets_medium:
            return "medium"
        
        return "low"
    
    def _generate_page_recommendations(self, page: Dict[str, Any], factors: Dict[str, Any], noindex_reasons: List[str]) -> List[str]:
        """Generate recommendations for page improvement"""
        
        recommendations = []
        
        # Recommendations based on factors
        if factors["word_count"] < self.indexing_rules["min_word_count"]:
            recommendations.append(f"Increase word count to {self.indexing_rules['min_word_count']}+ words")
        
        if factors["internal_links"] < self.indexing_rules["min_internal_links"]:
            recommendations.append(f"Add {self.indexing_rules['min_internal_links']}+ internal links")
        
        if factors["content_quality"] < 0.7:
            recommendations.append("Improve content quality with more comprehensive information")
        
        if factors["uniqueness_score"] < self.indexing_rules["min_uniqueness_score"]:
            recommendations.append("Increase content uniqueness to avoid duplicate content issues")
        
        if factors["user_signals"] < self.indexing_rules["min_user_signals"]:
            recommendations.append("Improve user engagement to increase user signals")
        
        # Recommendations based on noindex reasons
        for reason in noindex_reasons:
            if "Low word count" in reason:
                recommendations.append("Expand content to meet minimum word count requirements")
            elif "Low uniqueness" in reason:
                recommendations.append("Rewrite content to improve uniqueness")
            elif "High duplicate intent" in reason:
                recommendations.append("Differentiate content to reduce duplicate intent")
            elif "Orphan page" in reason:
                recommendations.append("Add internal links to connect with site structure")
            elif "Page too new" in reason:
                recommendations.append("Wait for page to mature before indexing")
        
        return recommendations
    
    def _categorize_priority_pages(self, indexable_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Categorize pages by priority"""
        
        priority_pages = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        for page in indexable_pages:
            priority = page.get("priority", "low")
            priority_pages[priority].append(page)
        
        return priority_pages
    
    def _analyze_noindex_reasons(self, noindex_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze noindex reasons"""
        
        analysis = {
            "total_noindex": len(noindex_pages),
            "reason_distribution": {},
            "page_type_distribution": {},
            "common_issues": []
        }
        
        # Count reasons
        reason_counts = {}
        for page in noindex_pages:
            for reason in page.get("noindex_reasons", []):
                reason_type = reason.split(":")[0]
                reason_counts[reason_type] = reason_counts.get(reason_type, 0) + 1
        
        analysis["reason_distribution"] = reason_counts
        
        # Count by page type
        type_counts = {}
        for page in noindex_pages:
            page_type = page["page_info"]["type"]
            type_counts[page_type] = type_counts.get(page_type, 0) + 1
        
        analysis["page_type_distribution"] = type_counts
        
        # Find common issues
        for reason, count in reason_counts.items():
            if count > len(noindex_pages) * 0.2:  # Issue affecting >20% of noindex pages
                analysis["common_issues"].append({
                    "issue": reason,
                    "affected_pages": count,
                    "percentage": (count / len(noindex_pages)) * 100
                })
        
        return analysis
    
    def _calculate_quality_metrics(self, page_evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality metrics"""
        
        metrics = {
            "average_quality_score": 0.0,
            "quality_distribution": {},
            "factor_averages": {},
            "pages_by_quality": {
                "excellent": 0,  # >= 90
                "good": 0,       # 70-89
                "fair": 0,       # 50-69
                "poor": 0        # < 50
            }
        }
        
        if not page_evaluations:
            return metrics
        
        # Calculate average quality score
        quality_scores = [p["quality_score"] for p in page_evaluations]
        metrics["average_quality_score"] = sum(quality_scores) / len(quality_scores)
        
        # Quality distribution
        for score in quality_scores:
            if score >= 90:
                metrics["pages_by_quality"]["excellent"] += 1
            elif score >= 70:
                metrics["pages_by_quality"]["good"] += 1
            elif score >= 50:
                metrics["pages_by_quality"]["fair"] += 1
            else:
                metrics["pages_by_quality"]["poor"] += 1
        
        # Factor averages
        all_factors = defaultdict(list)
        for evaluation in page_evaluations:
            for factor, value in evaluation["indexing_factors"].items():
                all_factors[factor].append(value)
        
        for factor, values in all_factors.items():
            if isinstance(values[0], (int, float)):
                metrics["factor_averages"][factor] = sum(values) / len(values)
            else:
                metrics["factor_averages"][factor] = values[0]  # For boolean values
        
        return metrics
    
    def _generate_indexing_recommendations(self, evaluation_report: Dict[str, Any]) -> List[str]:
        """Generate indexing recommendations"""
        
        recommendations = []
        
        # Overall recommendations
        indexable_rate = (evaluation_report["indexable_pages"] / evaluation_report["total_pages"]) * 100 if evaluation_report["total_pages"] > 0 else 0
        
        if indexable_rate < 50:
            recommendations.append("Low indexable rate - significant content quality improvements needed")
        elif indexable_rate < 70:
            recommendations.append("Moderate indexable rate - focus on improving content quality")
        else:
            recommendations.append("Good indexable rate - maintain current quality standards")
        
        # Noindex analysis recommendations
        noindex_analysis = evaluation_report["noindex_analysis"]
        
        for issue in noindex_analysis.get("common_issues", []):
            if "Low word count" in issue["issue"]:
                recommendations.append("Expand content to meet minimum word count requirements")
            elif "Low uniqueness" in issue["issue"]:
                recommendations.append("Improve content uniqueness to reduce duplicate content")
            elif "Orphan page" in issue["issue"]:
                recommendations.append("Fix orphan pages by adding internal links")
        
        # Quality metrics recommendations
        quality_metrics = evaluation_report["quality_metrics"]
        
        if quality_metrics["average_quality_score"] < 70:
            recommendations.append("Improve overall content quality across the platform")
        
        poor_quality_pages = quality_metrics["pages_by_quality"]["poor"]
        if poor_quality_pages > evaluation_report["total_pages"] * 0.2:
            recommendations.append("Focus on improving poor quality pages")
        
        # Priority recommendations
        priority_pages = evaluation_report["priority_pages"]
        
        if len(priority_pages.get("high", [])) < 10:
            recommendations.append("Create more high-priority content for immediate indexing")
        
        return recommendations
    
    def _create_implementation_plan(self, evaluation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Create implementation plan"""
        
        plan = {
            "immediate_actions": [],
            "short_term_goals": [],
            "long_term_strategy": [],
            "success_metrics": {},
            "timeline": {}
        }
        
        # Immediate actions (first week)
        plan["immediate_actions"] = [
            "Apply noindex to low-quality pages identified",
            "Add meta robots tags to pages with duplicate intent",
            "Fix orphan pages by adding internal links",
            "Improve content on pages below quality threshold"
        ]
        
        # Short-term goals (1 month)
        plan["short_term_goals"] = [
            "Achieve 70% indexable rate",
            "Reduce duplicate intent pages to <5%",
            "Increase average content quality score to 75+",
            "Create 20+ high-priority pages"
        ]
        
        # Long-term strategy (3-6 months)
        plan["long_term_strategy"] = [
            "Maintain 80%+ indexable rate",
            "Establish automated quality monitoring",
            "Create comprehensive authority page network",
            "Implement smart indexing automation"
        ]
        
        # Success metrics
        plan["success_metrics"] = {
            "indexable_rate_target": 80,
            "average_quality_target": 75,
            "noindex_rate_target": 20,
            "high_priority_pages_target": 50,
            "duplicate_intent_target": 5
        }
        
        # Timeline
        plan["timeline"] = {
            "week_1": "Apply noindex rules and fix critical issues",
            "week_2": "Improve content quality on low-scoring pages",
            "month_1": "Achieve short-term goals",
            "month_3": "Implement long-term strategy",
            "month_6": "Maintain and optimize indexing strategy"
        }
        
        return plan
    
    def get_indexing_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive indexing dashboard"""
        
        dashboard = {
            "summary": {},
            "indexing_status": {},
            "quality_analysis": {},
            "noindex_analysis": {},
            "priority_analysis": {},
            "recommendations": []
        }
        
        # Get latest evaluation data
        evaluation_data = cache.get("smart_indexing_strategy")
        if not evaluation_data:
            evaluation_data = self.evaluate_indexing_strategy()
        
        # Summary metrics
        dashboard["summary"] = {
            "total_pages": evaluation_data["total_pages"],
            "indexable_pages": evaluation_data["indexable_pages"],
            "noindex_pages": evaluation_data["noindex_pages"],
            "indexable_rate": (evaluation_data["indexable_pages"] / evaluation_data["total_pages"]) * 100 if evaluation_data["total_pages"] > 0 else 0,
            "average_quality": evaluation_data["quality_metrics"]["average_quality_score"]
        }
        
        # Indexing status
        dashboard["indexing_status"] = {
            "status": "healthy" if dashboard["summary"]["indexable_rate"] >= 70 else "needs_improvement",
            "priority_distribution": evaluation_data["priority_pages"],
            "last_evaluation": evaluation_data["evaluation_timestamp"]
        }
        
        # Quality analysis
        dashboard["quality_analysis"] = evaluation_data["quality_metrics"]
        
        # Noindex analysis
        dashboard["noindex_analysis"] = evaluation_data["noindex_analysis"]
        
        # Priority analysis
        dashboard["priority_analysis"] = {
            "high_priority_count": len(evaluation_data["priority_pages"].get("high", [])),
            "medium_priority_count": len(evaluation_data["priority_pages"].get("medium", [])),
            "low_priority_count": len(evaluation_data["priority_pages"].get("low", []))
        }
        
        # Recommendations
        dashboard["recommendations"] = evaluation_data["indexing_recommendations"]
        
        return dashboard


# Singleton instance
smart_indexing_strategy = SmartIndexingStrategy()
