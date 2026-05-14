"""
Analytics Priority Tracking System
Tracks pages generating impressions, clicks, backlinks, highest CTR, and pages with low engagement
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
from collections import defaultdict


class AnalyticsPriority:
    """Analytics priority tracking system"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 6  # 6 hours
        
        # Priority thresholds
        self.priority_thresholds = {
            "min_impressions": 100,          # Minimum impressions to track
            "min_clicks": 10,                # Minimum clicks to track
            "min_ctr": 0.02,                 # Minimum CTR (2%)
            "high_ctr_threshold": 0.05,      # High CTR threshold (5%)
            "low_engagement_threshold": 0.5,  # Low engagement threshold
            "backlink_potential_threshold": 3, # Minimum backlink potential
            "trending_threshold": 1.5,        # Growth rate for trending
            "decline_threshold": 0.8          # Decline rate for underperforming
        }
        
        # Tracking periods
        self.tracking_periods = {
            "daily": 7,       # Last 7 days
            "weekly": 4,      # Last 4 weeks
            "monthly": 3,     # Last 3 months
            "quarterly": 2    # Last 2 quarters
        }
        
        # Priority categories
        self.priority_categories = {
            "top_performers": {
                "description": "Pages with highest impressions and clicks",
                "weight": 0.3
            },
            "high_ctr_pages": {
                "description": "Pages with exceptional click-through rates",
                "weight": 0.25
            },
            "backlink_magnets": {
                "description": "Pages generating the most backlinks",
                "weight": 0.2
            },
            "trending_pages": {
                "description": "Pages with rapid growth",
                "weight": 0.15
            },
            "engagement_gaps": {
                "description": "Pages with low engagement needing attention",
                "weight": 0.1
            }
        }
    
    def track_analytics_priority(self) -> Dict[str, Any]:
        """Track analytics priority across all pages"""
        
        tracking_report = {
            "tracking_timestamp": datetime.now().isoformat(),
            "pages_analyzed": 0,
            "priority_categories": {},
            "top_performers": [],
            "high_ctr_pages": [],
            "backlink_magnets": [],
            "trending_pages": [],
            "engagement_gaps": [],
            "performance_insights": {},
            "action_recommendations": [],
            "tracking_score": 0.0,
            "time_taken": 0
        }
        
        start_time = time.time()
        
        # Get analytics data for all pages
        analytics_data = self._get_analytics_data()
        tracking_report["pages_analyzed"] = len(analytics_data)
        
        # Analyze top performers
        top_performers = self._analyze_top_performers(analytics_data)
        tracking_report["top_performers"] = top_performers
        tracking_report["priority_categories"]["top_performers"] = {
            "count": len(top_performers),
            "data": top_performers[:20]  # Top 20
        }
        
        # Analyze high CTR pages
        high_ctr_pages = self._analyze_high_ctr_pages(analytics_data)
        tracking_report["high_ctr_pages"] = high_ctr_pages
        tracking_report["priority_categories"]["high_ctr_pages"] = {
            "count": len(high_ctr_pages),
            "data": high_ctr_pages[:20]
        }
        
        # Analyze backlink magnets
        backlink_magnets = self._analyze_backlink_magnets(analytics_data)
        tracking_report["backlink_magnets"] = backlink_magnets
        tracking_report["priority_categories"]["backlink_magnets"] = {
            "count": len(backlink_magnets),
            "data": backlink_magnets[:20]
        }
        
        # Analyze trending pages
        trending_pages = self._analyze_trending_pages(analytics_data)
        tracking_report["trending_pages"] = trending_pages
        tracking_report["priority_categories"]["trending_pages"] = {
            "count": len(trending_pages),
            "data": trending_pages[:20]
        }
        
        # Analyze engagement gaps
        engagement_gaps = self._analyze_engagement_gaps(analytics_data)
        tracking_report["engagement_gaps"] = engagement_gaps
        tracking_report["priority_categories"]["engagement_gaps"] = {
            "count": len(engagement_gaps),
            "data": engagement_gaps[:20]
        }
        
        # Generate performance insights
        performance_insights = self._generate_performance_insights(tracking_report)
        tracking_report["performance_insights"] = performance_insights
        
        # Generate action recommendations
        action_recommendations = self._generate_action_recommendations(tracking_report)
        tracking_report["action_recommendations"] = action_recommendations
        
        # Calculate tracking score
        tracking_report["tracking_score"] = self._calculate_tracking_score(tracking_report)
        
        end_time = time.time()
        tracking_report["time_taken"] = end_time - start_time
        
        # Cache results
        cache.set("analytics_priority_tracking", tracking_report, self.cache_timeout)
        
        return tracking_report
    
    def _get_analytics_data(self) -> List[Dict[str, Any]]:
        """Get analytics data for all pages"""
        
        analytics_data = []
        
        # Get tools data
        tools = Tool.objects.filter(is_active=True).select_related('category')
        for tool in tools:
            # Simulate analytics data
            analytics = self._generate_analytics_data(tool, "tool")
            analytics_data.append(analytics)
        
        # Get SEO pages data
        seo_pages = SEOPage.objects.filter(is_active=True).select_related('category')
        for page in seo_pages:
            analytics = self._generate_analytics_data(page, "seo_page")
            analytics_data.append(analytics)
        
        # Get categories data
        categories = ToolCategory.objects.filter(is_active=True)
        for category in categories:
            analytics = self._generate_analytics_data(category, "category")
            analytics_data.append(analytics)
        
        # Get longtail variants data
        longtails = LongTailVariant.objects.filter(is_active=True).select_related('tool')
        for variant in longtails:
            analytics = self._generate_analytics_data(variant, "longtail")
            analytics_data.append(analytics)
        
        return analytics_data
    
    def _generate_analytics_data(self, model, page_type: str) -> Dict[str, Any]:
        """Generate analytics data for a page"""
        
        # Base metrics with random variation
        base_impressions = random.randint(50, 5000)
        base_ctr = random.uniform(0.01, 0.08)
        base_clicks = int(base_impressions * base_ctr)
        
        # Add type-specific variations
        if page_type == "tool":
            base_impressions = int(base_impressions * 1.2)  # Tools get more impressions
            base_ctr = base_ctr * 1.1  # Tools get higher CTR
        elif page_type == "category":
            base_impressions = int(base_impressions * 1.5)  # Categories get most impressions
            base_ctr = base_ctr * 0.9  # Categories get lower CTR
        elif page_type == "longtail":
            base_impressions = int(base_impressions * 0.7)  # Longtail gets fewer impressions
            base_ctr = base_ctr * 1.3  # Longtail gets higher CTR due to specificity
        
        # Calculate metrics
        clicks = int(base_impressions * base_ctr)
        ctr = (clicks / base_impressions) if base_impressions > 0 else 0
        
        # Engagement metrics
        avg_time_on_page = random.uniform(30, 300)  # 30 seconds to 5 minutes
        bounce_rate = random.uniform(0.3, 0.8)  # 30% to 80%
        pages_per_session = random.uniform(1.2, 3.5)  # 1.2 to 3.5 pages
        
        # Backlink data
        backlinks_count = random.randint(0, 50)
        referring_domains = random.randint(0, 20)
        
        # Growth data (trending calculation)
        current_period_impressions = base_impressions
        previous_period_impressions = int(base_impressions * random.uniform(0.7, 1.3))
        growth_rate = (current_period_impressions - previous_period_impressions) / previous_period_impressions if previous_period_impressions > 0 else 0
        
        # User signals
        shares = random.randint(0, 100)
        comments = random.randint(0, 50)
        likes = random.randint(0, 200)
        
        analytics = {
            "model": model,
            "page_type": page_type,
            "url": model.get_absolute_url(),
            "title": getattr(model, 'name', getattr(model, 'topic', getattr(model, 'title', ''))),
            "category": getattr(model.category, 'name', None) if hasattr(model, 'category') and model.category else None,
            "metrics": {
                "impressions": base_impressions,
                "clicks": clicks,
                "ctr": ctr,
                "avg_position": random.uniform(5, 50),
                "avg_time_on_page": avg_time_on_page,
                "bounce_rate": bounce_rate,
                "pages_per_session": pages_per_session,
                "conversion_rate": random.uniform(0.01, 0.1)
            },
            "backlinks": {
                "total_backlinks": backlinks_count,
                "referring_domains": referring_domains,
                "domain_authority_avg": random.uniform(10, 70),
                "new_backlinks": random.randint(0, 10)
            },
            "growth": {
                "current_period": current_period_impressions,
                "previous_period": previous_period_impressions,
                "growth_rate": growth_rate,
                "trend": "up" if growth_rate > 0.1 else "down" if growth_rate < -0.1 else "stable"
            },
            "engagement": {
                "shares": shares,
                "comments": comments,
                "likes": likes,
                "user_signals_score": (shares * 2 + comments * 3 + likes) / 100
            },
            "performance_score": 0.0  # Will be calculated
        }
        
        # Calculate performance score
        analytics["performance_score"] = self._calculate_performance_score(analytics)
        
        return analytics
    
    def _calculate_performance_score(self, analytics: Dict[str, Any]) -> float:
        """Calculate overall performance score"""
        
        score = 0.0
        
        # Impressions contribution (25%)
        impressions_score = min(analytics["metrics"]["impressions"] / 1000, 1.0)
        score += impressions_score * 0.25
        
        # CTR contribution (20%)
        ctr_score = min(analytics["metrics"]["ctr"] / 0.05, 1.0)  # Normalize to 5% CTR
        score += ctr_score * 0.20
        
        # Backlinks contribution (20%)
        backlinks_score = min(analytics["backlinks"]["total_backlinks"] / 20, 1.0)
        score += backlinks_score * 0.20
        
        # Growth contribution (15%)
        growth_rate = analytics["growth"]["growth_rate"]
        growth_score = max(min(growth_rate / 0.5, 1.0), 0)  # Normalize to 50% growth
        score += growth_score * 0.15
        
        # Engagement contribution (10%)
        engagement_score = min(analytics["engagement"]["user_signals_score"] / 5, 1.0)
        score += engagement_score * 0.10
        
        # Time on page contribution (10%)
        time_score = min(analytics["metrics"]["avg_time_on_page"] / 180, 1.0)  # Normalize to 3 minutes
        score += time_score * 0.10
        
        return score * 100  # Convert to 0-100 scale
    
    def _analyze_top_performers(self, analytics_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze top performing pages"""
        
        # Filter pages with minimum thresholds
        qualified_pages = [
            page for page in analytics_data
            if (page["metrics"]["impressions"] >= self.priority_thresholds["min_impressions"] and
                page["metrics"]["clicks"] >= self.priority_thresholds["min_clicks"])
        ]
        
        # Sort by combined performance (impressions + clicks)
        top_performers = sorted(
            qualified_pages,
            key=lambda x: (x["metrics"]["impressions"] * 0.6 + x["metrics"]["clicks"] * 0.4),
            reverse=True
        )
        
        # Add ranking and insights
        for i, page in enumerate(top_performers):
            page["ranking"] = i + 1
            page["insights"] = self._generate_top_performer_insights(page)
        
        return top_performers
    
    def _analyze_high_ctr_pages(self, analytics_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze pages with high CTR"""
        
        # Filter pages with high CTR and minimum impressions
        high_ctr_pages = [
            page for page in analytics_data
            if (page["metrics"]["ctr"] >= self.priority_thresholds["high_ctr_threshold"] and
                page["metrics"]["impressions"] >= self.priority_thresholds["min_impressions"])
        ]
        
        # Sort by CTR
        high_ctr_pages = sorted(high_ctr_pages, key=lambda x: x["metrics"]["ctr"], reverse=True)
        
        # Add ranking and insights
        for i, page in enumerate(high_ctr_pages):
            page["ranking"] = i + 1
            page["insights"] = self._generate_high_ctr_insights(page)
        
        return high_ctr_pages
    
    def _analyze_backlink_magnets(self, analytics_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze pages that are backlink magnets"""
        
        # Filter pages with significant backlinks
        backlink_magnets = [
            page for page in analytics_data
            if page["backlinks"]["total_backlinks"] >= self.priority_thresholds["backlink_potential_threshold"]
        ]
        
        # Sort by backlink count and domain authority
        backlink_magnets = sorted(
            backlink_magnets,
            key=lambda x: (x["backlinks"]["total_backlinks"] * 0.7 + x["backlinks"]["domain_authority_avg"] * 0.3),
            reverse=True
        )
        
        # Add ranking and insights
        for i, page in enumerate(backlink_magnets):
            page["ranking"] = i + 1
            page["insights"] = self._generate_backlink_insights(page)
        
        return backlink_magnets
    
    def _analyze_trending_pages(self, analytics_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze trending pages with rapid growth"""
        
        # Filter pages with significant growth
        trending_pages = [
            page for page in analytics_data
            if page["growth"]["growth_rate"] >= self.priority_thresholds["trending_threshold"]
        ]
        
        # Sort by growth rate
        trending_pages = sorted(trending_pages, key=lambda x: x["growth"]["growth_rate"], reverse=True)
        
        # Add ranking and insights
        for i, page in enumerate(trending_pages):
            page["ranking"] = i + 1
            page["insights"] = self._generate_trending_insights(page)
        
        return trending_pages
    
    def _analyze_engagement_gaps(self, analytics_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze pages with engagement gaps"""
        
        # Filter pages with low engagement but decent traffic
        engagement_gaps = [
            page for page in analytics_data
            if (page["metrics"]["impressions"] >= self.priority_thresholds["min_impressions"] and
                page["engagement"]["user_signals_score"] < self.priority_thresholds["low_engagement_threshold"])
        ]
        
        # Sort by opportunity (high impressions, low engagement)
        engagement_gaps = sorted(
            engagement_gaps,
            key=lambda x: x["metrics"]["impressions"] / (x["engagement"]["user_signals_score"] + 0.1),
            reverse=True
        )
        
        # Add ranking and insights
        for i, page in enumerate(engagement_gaps):
            page["ranking"] = i + 1
            page["insights"] = self._generate_engagement_gap_insights(page)
        
        return engagement_gaps
    
    def _generate_top_performer_insights(self, page: Dict[str, Any]) -> List[str]:
        """Generate insights for top performers"""
        
        insights = []
        
        # Traffic insight
        if page["metrics"]["impressions"] > 2000:
            insights.append("High traffic volume indicates strong demand")
        
        # CTR insight
        if page["metrics"]["ctr"] > 0.04:
            insights.append("Exceptional click-through rate shows compelling content")
        
        # Backlink insight
        if page["backlinks"]["total_backlinks"] > 20:
            insights.append("Strong backlink profile indicates authority")
        
        # Growth insight
        if page["growth"]["growth_rate"] > 0.2:
            insights.append("Rapid growth trajectory")
        
        # Engagement insight
        if page["engagement"]["user_signals_score"] > 3:
            insights.append("High user engagement indicates value")
        
        return insights
    
    def _generate_high_ctr_insights(self, page: Dict[str, Any]) -> List[str]:
        """Generate insights for high CTR pages"""
        
        insights = []
        
        # CTR analysis
        if page["metrics"]["ctr"] > 0.08:
            insights.append("Exceptional CTR - highly optimized for search intent")
        elif page["metrics"]["ctr"] > 0.06:
            insights.append("Strong CTR - well-aligned with user intent")
        
        # Position analysis
        if page["metrics"]["avg_position"] < 10:
            insights.append("Top rankings driving high CTR")
        elif page["metrics"]["avg_position"] > 20 and page["metrics"]["ctr"] > 0.05:
            insights.append("High CTR despite lower rankings - compelling title/meta")
        
        # Traffic quality
        if page["metrics"]["bounce_rate"] < 0.5:
            insights.append("Low bounce rate indicates quality traffic")
        
        return insights
    
    def _generate_backlink_insights(self, page: Dict[str, Any]) -> List[str]:
        """Generate insights for backlink magnets"""
        
        insights = []
        
        # Backlink quantity
        if page["backlinks"]["total_backlinks"] > 30:
            insights.append("Strong backlink acquisition")
        
        # Domain authority
        if page["backlinks"]["domain_authority_avg"] > 50:
            insights.append("High-quality referring domains")
        
        # New backlinks
        if page["backlinks"]["new_backlinks"] > 5:
            insights.append("Active backlink growth")
        
        # Content type insight
        if page["page_type"] == "seo_page":
            insights.append("SEO content attracting backlinks")
        elif page["page_type"] == "tool":
            insights.append("Tool page generating natural backlinks")
        
        return insights
    
    def _generate_trending_insights(self, page: Dict[str, Any]) -> List[str]:
        """Generate insights for trending pages"""
        
        insights = []
        
        # Growth rate
        if page["growth"]["growth_rate"] > 2.0:
            insights.append("Explosive growth - viral potential")
        elif page["growth"]["growth_rate"] > 1.0:
            insights.append("Strong upward trend")
        
        # Traffic increase
        if page["metrics"]["impressions"] > 1000:
            insights.append("Significant traffic increase")
        
        # Seasonal insight
        if page["category"] in ["Resume", "CV"]:
            insights.append("Seasonal trend - job search season")
        
        return insights
    
    def _generate_engagement_gap_insights(self, page: Dict[str, Any]) -> List[str]:
        """Generate insights for engagement gaps"""
        
        insights = []
        
        # Low engagement indicators
        if page["metrics"]["bounce_rate"] > 0.7:
            insights.append("High bounce rate - content mismatch")
        
        if page["metrics"]["avg_time_on_page"] < 60:
            insights.append("Low time on page - content not engaging")
        
        if page["engagement"]["shares"] < 5:
            insights.append("Low share rate - not compelling enough to share")
        
        # Opportunity insight
        if page["metrics"]["impressions"] > 1000:
            insights.append("High traffic with low engagement - optimization opportunity")
        
        # Content type insight
        if page["page_type"] == "longtail":
            insights.append("Longtail page needs better content")
        
        return insights
    
    def _generate_performance_insights(self, tracking_report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall performance insights"""
        
        insights = {
            "overall_performance": {},
            "category_performance": {},
            "trending_analysis": {},
            "opportunity_areas": {}
        }
        
        # Overall performance
        total_pages = tracking_report["pages_analyzed"]
        top_performers_count = len(tracking_report["top_performers"])
        high_ctr_count = len(tracking_report["high_ctr_pages"])
        backlink_magnets_count = len(tracking_report["backlink_magnets"])
        
        insights["overall_performance"] = {
            "pages_with_significant_traffic": top_performers_count,
            "pages_with_high_ctr": high_ctr_count,
            "pages_with_strong_backlinks": backlink_magnets_count,
            "top_performer_rate": (top_performers_count / total_pages * 100) if total_pages > 0 else 0,
            "high_ctr_rate": (high_ctr_count / total_pages * 100) if total_pages > 0 else 0,
            "backlink_magnet_rate": (backlink_magnets_count / total_pages * 100) if total_pages > 0 else 0
        }
        
        # Category performance
        category_performance = defaultdict(lambda: {"count": 0, "total_performance": 0})
        
        for category_data in tracking_report["top_performers"]:
            category = category_data.get("category", "Unknown")
            category_performance[category]["count"] += 1
            category_performance[category]["total_performance"] += category_data["performance_score"]
        
        # Calculate averages
        for category, data in category_performance.items():
            if data["count"] > 0:
                data["avg_performance"] = data["total_performance"] / data["count"]
        
        insights["category_performance"] = dict(category_performance)
        
        # Trending analysis
        trending_pages = tracking_report["trending_pages"]
        if trending_pages:
            avg_growth_rate = sum(page["growth"]["growth_rate"] for page in trending_pages) / len(trending_pages)
            insights["trending_analysis"] = {
                "trending_pages_count": len(trending_pages),
                "avg_growth_rate": avg_growth_rate,
                "growth_distribution": self._analyze_growth_distribution(trending_pages)
            }
        
        # Opportunity areas
        engagement_gaps = tracking_report["engagement_gaps"]
        if engagement_gaps:
            total_lost_opportunities = sum(page["metrics"]["impressions"] for page in engagement_gaps)
            insights["opportunity_areas"] = {
                "pages_needing_attention": len(engagement_gaps),
                "total_impression_opportunity": total_lost_opportunities,
                "potential_ctr_improvement": total_lost_opportunities * 0.02  # 2% CTR improvement potential
            }
        
        return insights
    
    def _analyze_growth_distribution(self, trending_pages: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze growth distribution"""
        
        distribution = {
            "explosive": 0,    # > 200% growth
            "rapid": 0,        # 100-200% growth
            "moderate": 0,     # 50-100% growth
            "slight": 0        # 20-50% growth
        }
        
        for page in trending_pages:
            growth_rate = page["growth"]["growth_rate"]
            
            if growth_rate > 2.0:
                distribution["explosive"] += 1
            elif growth_rate > 1.0:
                distribution["rapid"] += 1
            elif growth_rate > 0.5:
                distribution["moderate"] += 1
            else:
                distribution["slight"] += 1
        
        return distribution
    
    def _generate_action_recommendations(self, tracking_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Top performer recommendations
        top_performers = tracking_report["top_performers"][:5]
        if top_performers:
            recommendations.append({
                "category": "top_performers",
                "priority": "high",
                "action": "Double down on top performers",
                "description": "Invest more resources in pages already performing well",
                "pages": [page["title"] for page in top_performers],
                "expected_impact": "20-30% traffic increase"
            })
        
        # High CTR recommendations
        high_ctr_pages = tracking_report["high_ctr_pages"][:5]
        if high_ctr_pages:
            recommendations.append({
                "category": "high_ctr",
                "priority": "high",
                "action": "Scale high CTR strategies",
                "description": "Apply successful title/meta patterns to similar pages",
                "pages": [page["title"] for page in high_ctr_pages],
                "expected_impact": "15-25% CTR improvement"
            })
        
        # Backlink magnet recommendations
        backlink_magnets = tracking_report["backlink_magnets"][:5]
        if backlink_magnets:
            recommendations.append({
                "category": "backlinks",
                "priority": "medium",
                "action": "Promote backlink magnets",
                "description": "Increase visibility of pages that attract backlinks",
                "pages": [page["title"] for page in backlink_magnets],
                "expected_impact": "10-20 new backlinks"
            })
        
        # Trending page recommendations
        trending_pages = tracking_report["trending_pages"][:5]
        if trending_pages:
            recommendations.append({
                "category": "trending",
                "priority": "high",
                "action": "Accelerate trending pages",
                "description": "Invest in pages showing rapid growth",
                "pages": [page["title"] for page in trending_pages],
                "expected_impact": "50-100% growth continuation"
            })
        
        # Engagement gap recommendations
        engagement_gaps = tracking_report["engagement_gaps"][:5]
        if engagement_gaps:
            recommendations.append({
                "category": "engagement",
                "priority": "medium",
                "action": "Fix engagement gaps",
                "description": "Improve content on pages with traffic but low engagement",
                "pages": [page["title"] for page in engagement_gaps],
                "expected_impact": "2-3x engagement improvement"
            })
        
        return recommendations
    
    def _calculate_tracking_score(self, tracking_report: Dict[str, Any]) -> float:
        """Calculate overall tracking score"""
        
        score = 100.0
        
        # Deduct for low top performer rate
        total_pages = tracking_report["pages_analyzed"]
        top_performers_count = len(tracking_report["top_performers"])
        top_performer_rate = (top_performers_count / total_pages) * 100 if total_pages > 0 else 0
        
        if top_performer_rate < 10:
            score -= 20
        elif top_performer_rate < 20:
            score -= 10
        
        # Deduct for low high CTR rate
        high_ctr_count = len(tracking_report["high_ctr_pages"])
        high_ctr_rate = (high_ctr_count / total_pages) * 100 if total_pages > 0 else 0
        
        if high_ctr_rate < 5:
            score -= 15
        elif high_ctr_rate < 10:
            score -= 5
        
        # Deduct for high engagement gap rate
        engagement_gaps_count = len(tracking_report["engagement_gaps"])
        engagement_gap_rate = (engagement_gaps_count / total_pages) * 100 if total_pages > 0 else 0
        
        if engagement_gap_rate > 30:
            score -= 15
        elif engagement_gap_rate > 20:
            score -= 5
        
        # Bonus for good backlink magnet rate
        backlink_magnets_count = len(tracking_report["backlink_magnets"])
        backlink_magnet_rate = (backlink_magnets_count / total_pages) * 100 if total_pages > 0 else 0
        
        if backlink_magnet_rate > 15:
            score += 10
        elif backlink_magnet_rate > 10:
            score += 5
        
        # Bonus for trending pages
        trending_count = len(tracking_report["trending_pages"])
        if trending_count > 20:
            score += 10
        elif trending_count > 10:
            score += 5
        
        return max(score, 0)
    
    def get_analytics_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard"""
        
        dashboard = {
            "summary": {},
            "priority_overview": {},
            "performance_metrics": {},
            "trending_analysis": {},
            "opportunity_analysis": {},
            "recommendations": []
        }
        
        # Get latest tracking data
        tracking_data = cache.get("analytics_priority_tracking")
        if not tracking_data:
            tracking_data = self.track_analytics_priority()
        
        # Summary metrics
        dashboard["summary"] = {
            "total_pages": tracking_data["pages_analyzed"],
            "tracking_score": tracking_data["tracking_score"],
            "top_performers": len(tracking_data["top_performers"]),
            "high_ctr_pages": len(tracking_data["high_ctr_pages"]),
            "backlink_magnets": len(tracking_data["backlink_magnets"]),
            "trending_pages": len(tracking_data["trending_pages"]),
            "engagement_gaps": len(tracking_data["engagement_gaps"])
        }
        
        # Priority overview
        dashboard["priority_overview"] = tracking_data["priority_categories"]
        
        # Performance metrics
        dashboard["performance_metrics"] = tracking_data["performance_insights"]
        
        # Trending analysis
        dashboard["trending_analysis"] = {
            "trending_pages": tracking_data["trending_pages"][:10],
            "growth_insights": tracking_data["performance_insights"].get("trending_analysis", {})
        }
        
        # Opportunity analysis
        dashboard["opportunity_analysis"] = {
            "engagement_gaps": tracking_data["engagement_gaps"][:10],
            "opportunity_areas": tracking_data["performance_insights"].get("opportunity_areas", {})
        }
        
        # Recommendations
        dashboard["recommendations"] = tracking_data["action_recommendations"]
        
        return dashboard


# Singleton instance
analytics_priority = AnalyticsPriority()
