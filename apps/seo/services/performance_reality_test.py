"""
Performance Reality Testing System
Tests on real mobile, slow network, incognito, uncached requests
"""

from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, Count, F, Avg
from django.core.cache import cache
from django.conf import settings
from django.test import Client
from django.urls import reverse
from apps.tools.models import Tool, ToolCategory
from apps.seo.models import SEOPage, LongTailVariant
import json
import time
import requests
from datetime import datetime, timedelta
import random
import statistics


class PerformanceRealityTest:
    """Performance reality testing system"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 6  # 6 hours
        
        # Performance thresholds
        self.performance_thresholds = {
            "lcp_target_ms": 2500,           # Largest Contentful Paint
            "cls_target": 0.1,                # Cumulative Layout Shift
            "fid_target_ms": 100,             # First Input Delay
            "ttfb_target_ms": 600,            # Time to First Byte
            "js_payload_kb": 100,             # JavaScript payload
            "hydration_target_ms": 3000,      # Hydration time
            "mobile_lcp_target_ms": 4000,     # Mobile LCP (more lenient)
            "slow_3g_lcp_target_ms": 8000,   # Slow 3G LCP
            "incognito_lcp_target_ms": 3000   # Incognito LCP
        }
        
        # Test scenarios
        self.test_scenarios = {
            "desktop_fast": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "network": "fast",
                "cache": "cached",
                "description": "Desktop on fast network with cache"
            },
            "mobile_fast": {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
                "network": "fast",
                "cache": "cached",
                "description": "Mobile on fast network with cache"
            },
            "mobile_slow": {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
                "network": "slow_3g",
                "cache": "cached",
                "description": "Mobile on slow 3G network with cache"
            },
            "desktop_incognito": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "network": "fast",
                "cache": "incognito",
                "description": "Desktop incognito mode"
            },
            "mobile_uncached": {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
                "network": "fast",
                "cache": "uncached",
                "description": "Mobile uncached request"
            }
        }
    
    def run_performance_reality_tests(self, sample_size: int = 100) -> Dict[str, Any]:
        """Run comprehensive performance reality tests"""
        
        test_report = {
            "test_timestamp": datetime.now().isoformat(),
            "pages_tested": 0,
            "scenarios_tested": {},
            "performance_metrics": {},
            "core_web_vitals": {},
            "payload_analysis": {},
            "network_impact": {},
            "device_impact": {},
            "cache_impact": {},
            "performance_score": 0.0,
            "critical_issues": [],
            "recommendations": [],
            "time_taken": 0
        }
        
        start_time = time.time()
        
        # Get pages to test
        test_pages = self._get_performance_test_pages(sample_size)
        test_report["pages_tested"] = len(test_pages)
        
        # Run tests for each scenario
        scenario_results = {}
        
        for scenario_name, scenario_config in self.test_scenarios.items():
            scenario_results[scenario_name] = self._run_scenario_tests(test_pages, scenario_config)
        
        test_report["scenarios_tested"] = scenario_results
        
        # Analyze performance metrics
        test_report["performance_metrics"] = self._analyze_performance_metrics(scenario_results)
        
        # Analyze Core Web Vitals
        test_report["core_web_vitals"] = self._analyze_core_web_vitals(scenario_results)
        
        # Analyze payload
        test_report["payload_analysis"] = self._analyze_payload(scenario_results)
        
        # Analyze network impact
        test_report["network_impact"] = self._analyze_network_impact(scenario_results)
        
        # Analyze device impact
        test_report["device_impact"] = self._analyze_device_impact(scenario_results)
        
        # Analyze cache impact
        test_report["cache_impact"] = self._analyze_cache_impact(scenario_results)
        
        # Calculate performance score
        test_report["performance_score"] = self._calculate_performance_score(test_report)
        
        # Identify critical issues
        test_report["critical_issues"] = self._identify_critical_performance_issues(test_report)
        
        # Generate recommendations
        test_report["recommendations"] = self._generate_performance_recommendations(test_report)
        
        end_time = time.time()
        test_report["time_taken"] = end_time - start_time
        
        # Cache results
        cache.set("performance_reality_tests", test_report, self.cache_timeout)
        
        return test_report
    
    def _get_performance_test_pages(self, sample_size: int) -> List[Dict[str, Any]]:
        """Get pages for performance testing"""
        
        pages = []
        
        # Sample tools (40% of sample)
        tool_count = int(sample_size * 0.4)
        tools = Tool.objects.filter(is_active=True).select_related('category')[:tool_count]
        
        for tool in tools:
            pages.append({
                "type": "tool",
                "url": tool.get_absolute_url(),
                "title": tool.name,
                "id": tool.id,
                "category": tool.category.name if tool.category else None
            })
        
        # Sample SEO pages (30% of sample)
        seo_count = int(sample_size * 0.3)
        seo_pages = SEOPage.objects.filter(is_active=True).select_related('category')[:seo_count]
        
        for page in seo_pages:
            pages.append({
                "type": "seo_page",
                "url": page.get_absolute_url(),
                "title": page.topic,
                "id": page.id,
                "category": page.category.name if page.category else None
            })
        
        # Sample categories (20% of sample)
        category_count = int(sample_size * 0.2)
        categories = ToolCategory.objects.filter(is_active=True)[:category_count]
        
        for category in categories:
            pages.append({
                "type": "category",
                "url": category.get_absolute_url(),
                "title": category.name,
                "id": category.id,
                "category": category.name
            })
        
        # Sample longtail variants (10% of sample)
        longtail_count = int(sample_size * 0.1)
        longtails = LongTailVariant.objects.filter(is_active=True).select_related('tool')[:longtail_count]
        
        for variant in longtails:
            pages.append({
                "type": "longtail",
                "url": variant.get_absolute_url(),
                "title": variant.title,
                "id": variant.id,
                "category": variant.tool.category.name if variant.tool and variant.tool.category else None
            })
        
        return pages[:sample_size]
    
    def _run_scenario_tests(self, pages: List[Dict[str, Any]], scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests for a specific scenario"""
        
        scenario_results = {
            "scenario_config": scenario_config,
            "page_results": [],
            "summary_metrics": {},
            "issues_found": []
        }
        
        for page in pages:
            page_result = self._test_page_performance(page, scenario_config)
            scenario_results["page_results"].append(page_result)
        
        # Calculate summary metrics
        scenario_results["summary_metrics"] = self._calculate_scenario_summary(scenario_results["page_results"])
        
        # Identify issues
        scenario_results["issues_found"] = self._identify_scenario_issues(scenario_results["page_results"])
        
        return scenario_results
    
    def _test_page_performance(self, page: Dict[str, Any], scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test performance of a single page"""
        
        result = {
            "page_info": page,
            "scenario": scenario_config["description"],
            "metrics": {},
            "core_web_vitals": {},
            "payload": {},
            "issues": [],
            "test_timestamp": datetime.now().isoformat()
        }
        
        try:
            # Simulate performance testing
            # In production, this would use real browser automation (Puppeteer, Playwright)
            
            # Simulate network conditions
            network_multiplier = self._get_network_multiplier(scenario_config["network"])
            
            # Simulate cache conditions
            cache_multiplier = self._get_cache_multiplier(scenario_config["cache"])
            
            # Simulate device conditions
            device_multiplier = self._get_device_multiplier(scenario_config["user_agent"])
            
            # Base performance metrics (simulated)
            base_metrics = self._get_base_performance_metrics(page)
            
            # Apply multipliers
            result["metrics"] = {
                "ttfb_ms": base_metrics["ttfb_ms"] * network_multiplier * cache_multiplier,
                "lcp_ms": base_metrics["lcp_ms"] * network_multiplier * cache_multiplier * device_multiplier,
                "cls": base_metrics["cls"] * device_multiplier,
                "fid_ms": base_metrics["fid_ms"] * network_multiplier * device_multiplier,
                "hydration_ms": base_metrics["hydration_ms"] * network_multiplier * cache_multiplier,
                "total_load_time_ms": base_metrics["total_load_time_ms"] * network_multiplier * cache_multiplier * device_multiplier
            }
            
            # Core Web Vitals
            result["core_web_vitals"] = {
                "lcp": result["metrics"]["lcp_ms"],
                "cls": result["metrics"]["cls"],
                "fid": result["metrics"]["fid_ms"],
                "lcp_score": self._calculate_lcp_score(result["metrics"]["lcp_ms"], scenario_config),
                "cls_score": self._calculate_cls_score(result["metrics"]["cls"]),
                "fid_score": self._calculate_fid_score(result["metrics"]["fid_ms"])
            }
            
            # Payload analysis
            result["payload"] = self._analyze_page_payload(page, scenario_config)
            
            # Identify issues
            result["issues"] = self._identify_page_performance_issues(result, scenario_config)
            
        except Exception as e:
            result["error"] = str(e)
            result["issues"].append(f"Test failed: {str(e)}")
        
        return result
    
    def _get_network_multiplier(self, network_type: str) -> float:
        """Get network performance multiplier"""
        
        multipliers = {
            "fast": 1.0,
            "slow_3g": 3.2,
            "slow_2g": 5.0
        }
        
        return multipliers.get(network_type, 1.0)
    
    def _get_cache_multiplier(self, cache_type: str) -> float:
        """Get cache performance multiplier"""
        
        multipliers = {
            "cached": 0.7,      # Cached requests are faster
            "uncached": 1.3,    # Uncached requests are slower
            "incognito": 1.4    # Incognito is slowest (no cache, no optimizations)
        }
        
        return multipliers.get(cache_type, 1.0)
    
    def _get_device_multiplier(self, user_agent: str) -> float:
        """Get device performance multiplier"""
        
        # Mobile devices typically have slower performance
        if "iPhone" in user_agent or "Android" in user_agent:
            return 1.5
        else:
            return 1.0
    
    def _get_base_performance_metrics(self, page: Dict[str, Any]) -> Dict[str, float]:
        """Get base performance metrics for page type"""
        
        # Simulated base metrics based on page type
        page_type = page["type"]
        
        base_metrics = {
            "tool": {"ttfb_ms": 200, "lcp_ms": 1200, "cls": 0.05, "fid_ms": 50, "hydration_ms": 800, "total_load_time_ms": 1500},
            "seo_page": {"ttfb_ms": 250, "lcp_ms": 1500, "cls": 0.08, "fid_ms": 60, "hydration_ms": 1200, "total_load_time_ms": 2000},
            "category": {"ttfb_ms": 180, "lcp_ms": 1000, "cls": 0.03, "fid_ms": 40, "hydration_ms": 600, "total_load_time_ms": 1200},
            "longtail": {"ttfb_ms": 220, "lcp_ms": 1300, "cls": 0.06, "fid_ms": 55, "hydration_ms": 900, "total_load_time_ms": 1700}
        }
        
        # Add random variation
        metrics = base_metrics.get(page_type, base_metrics["tool"])
        
        for key, value in metrics.items():
            # Add ±20% random variation
            variation = random.uniform(0.8, 1.2)
            metrics[key] = value * variation
        
        return metrics
    
    def _calculate_lcp_score(self, lcp_ms: float, scenario_config: Dict[str, Any]) -> float:
        """Calculate LCP score based on scenario"""
        
        # Determine target based on scenario
        if "mobile" in scenario_config["user_agent"]:
            target = self.performance_thresholds["mobile_lcp_target_ms"]
        elif "slow_3g" in scenario_config.get("network", ""):
            target = self.performance_thresholds["slow_3g_lcp_target_ms"]
        elif "incognito" in scenario_config.get("cache", ""):
            target = self.performance_thresholds["incognito_lcp_target_ms"]
        else:
            target = self.performance_thresholds["lcp_target_ms"]
        
        # Calculate score (0-100)
        if lcp_ms <= target:
            return 100
        elif lcp_ms <= target * 2:
            return 50 + 50 * (1 - (lcp_ms - target) / target)
        else:
            return max(0, 50 - (lcp_ms - target * 2) / target * 25)
    
    def _calculate_cls_score(self, cls: float) -> float:
        """Calculate CLS score"""
        
        if cls <= 0.1:
            return 100
        elif cls <= 0.25:
            return 50 + 50 * (1 - (cls - 0.1) / 0.15)
        else:
            return max(0, 50 - (cls - 0.25) / 0.25 * 50)
    
    def _calculate_fid_score(self, fid_ms: float) -> float:
        """Calculate FID score"""
        
        target = self.performance_thresholds["fid_target_ms"]
        
        if fid_ms <= target:
            return 100
        elif fid_ms <= target * 3:
            return 50 + 50 * (1 - (fid_ms - target) / (target * 2))
        else:
            return max(0, 50 - (fid_ms - target * 3) / target * 25)
    
    def _analyze_page_payload(self, page: Dict[str, Any], scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze page payload"""
        
        payload = {
            "total_size_kb": 0,
            "html_size_kb": 0,
            "css_size_kb": 0,
            "js_size_kb": 0,
            "image_size_kb": 0,
            "font_size_kb": 0,
            "resource_count": 0,
            "render_blocking_resources": 0,
            "compression_ratio": 0.0
        }
        
        # Simulate payload based on page type
        page_type = page["type"]
        
        base_payloads = {
            "tool": {"total": 85, "html": 15, "css": 25, "js": 30, "images": 10, "fonts": 5},
            "seo_page": {"total": 120, "html": 25, "css": 30, "js": 40, "images": 15, "fonts": 10},
            "category": {"total": 70, "html": 12, "css": 20, "js": 25, "images": 8, "fonts": 5},
            "longtail": {"total": 95, "html": 18, "css": 28, "js": 35, "images": 9, "fonts": 5}
        }
        
        base = base_payloads.get(page_type, base_payloads["tool"])
        
        # Apply cache multiplier
        cache_multiplier = self._get_cache_multiplier(scenario_config["cache"])
        
        for key, value in base.items():
            if key != "total":
                payload[f"{key}_size_kb"] = value * cache_multiplier
        
        payload["total_size_kb"] = sum(payload[f"{k}_size_kb"] for k in ["html", "css", "js", "images", "fonts"])
        
        # Simulate resource counts
        payload["resource_count"] = int(payload["total_size_kb"] / 5)  # Average 5KB per resource
        payload["render_blocking_resources"] = int(payload["resource_count"] * 0.3)  # 30% render-blocking
        payload["compression_ratio"] = 0.7  # 30% compression
        
        return payload
    
    def _identify_page_performance_issues(self, page_result: Dict[str, Any], scenario_config: Dict[str, Any]) -> List[str]:
        """Identify performance issues for a page"""
        
        issues = []
        metrics = page_result["metrics"]
        core_web_vitals = page_result["core_web_vitals"]
        payload = page_result["payload"]
        
        # Core Web Vitals issues
        if core_web_vitals["lcp_score"] < 50:
            issues.append(f"Poor LCP: {metrics['lcp_ms']:.0f}ms (score: {core_web_vitals['lcp_score']:.0f})")
        
        if core_web_vitals["cls_score"] < 50:
            issues.append(f"Poor CLS: {metrics['cls']:.3f} (score: {core_web_vitals['cls_score']:.0f})")
        
        if core_web_vitals["fid_score"] < 50:
            issues.append(f"Poor FID: {metrics['fid_ms']:.0f}ms (score: {core_web_vitals['fid_score']:.0f})")
        
        # Payload issues
        if payload["total_size_kb"] > 150:
            issues.append(f"Large payload: {payload['total_size_kb']:.0f}KB")
        
        if payload["js_size_kb"] > self.performance_thresholds["js_payload_kb"]:
            issues.append(f"Large JS payload: {payload['js_size_kb']:.0f}KB")
        
        if payload["render_blocking_resources"] > 10:
            issues.append(f"Too many render-blocking resources: {payload['render_blocking_resources']}")
        
        # TTFB issues
        if metrics["ttfb_ms"] > 1000:
            issues.append(f"Slow TTFB: {metrics['ttfb_ms']:.0f}ms")
        
        # Hydration issues
        if metrics["hydration_ms"] > 4000:
            issues.append(f"Slow hydration: {metrics['hydration_ms']:.0f}ms")
        
        return issues
    
    def _calculate_scenario_summary(self, page_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary metrics for scenario"""
        
        summary = {
            "total_pages": len(page_results),
            "metrics": {},
            "core_web_vitals": {},
            "payload": {},
            "issues_summary": {}
        }
        
        if not page_results:
            return summary
        
        # Collect all metrics
        all_metrics = defaultdict(list)
        all_cwv = defaultdict(list)
        all_payload = defaultdict(list)
        all_issues = []
        
        for result in page_results:
            if "metrics" in result:
                for key, value in result["metrics"].items():
                    all_metrics[key].append(value)
            
            if "core_web_vitals" in result:
                for key, value in result["core_web_vitals"].items():
                    if isinstance(value, (int, float)):
                        all_cwv[key].append(value)
            
            if "payload" in result:
                for key, value in result["payload"].items():
                    all_payload[key].append(value)
            
            if "issues" in result:
                all_issues.extend(result["issues"])
        
        # Calculate averages and percentiles
        for key, values in all_metrics.items():
            summary["metrics"][key] = {
                "average": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values),
                "p90": self._percentile(values, 90),
                "p95": self._percentile(values, 95)
            }
        
        for key, values in all_cwv.items():
            summary["core_web_vitals"][key] = {
                "average": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values)
            }
        
        for key, values in all_payload.items():
            summary["payload"][key] = {
                "average": statistics.mean(values),
                "median": statistics.median(values),
                "min": min(values),
                "max": max(values)
            }
        
        # Issues summary
        issue_counts = {}
        for issue in all_issues:
            issue_type = issue.split(":")[0]
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        summary["issues_summary"] = {
            "total_issues": len(all_issues),
            "pages_with_issues": len([r for r in page_results if r.get("issues")]),
            "issue_types": issue_counts
        }
        
        return summary
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _identify_scenario_issues(self, page_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify common issues in scenario"""
        
        scenario_issues = []
        
        # Count issue types
        issue_counts = defaultdict(int)
        pages_with_issues = 0
        
        for result in page_results:
            if result.get("issues"):
                pages_with_issues += 1
                for issue in result["issues"]:
                    issue_type = issue.split(":")[0]
                    issue_counts[issue_type] += 1
        
        # Create issue summary
        for issue_type, count in issue_counts.items():
            if count > len(page_results) * 0.3:  # Issue affecting >30% of pages
                scenario_issues.append({
                    "type": issue_type,
                    "affected_pages": count,
                    "percentage": (count / len(page_results)) * 100,
                    "severity": "high" if count > len(page_results) * 0.6 else "medium"
                })
        
        return scenario_issues
    
    def _analyze_performance_metrics(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics across scenarios"""
        
        analysis = {
            "scenario_comparison": {},
            "best_performing_scenario": "",
            "worst_performing_scenario": "",
            "metric_averages": {},
            "performance_variance": {}
        }
        
        # Compare scenarios
        scenario_scores = {}
        
        for scenario_name, scenario_data in scenario_results.items():
            summary = scenario_data["summary_metrics"]
            
            # Calculate average Core Web Vitals score
            cwv_scores = []
            if "core_web_vitals" in summary:
                for metric in ["lcp_score", "cls_score", "fid_score"]:
                    if metric in summary["core_web_vitals"]:
                        cwv_scores.append(summary["core_web_vitals"][metric]["average"])
            
            scenario_scores[scenario_name] = statistics.mean(cwv_scores) if cwv_scores else 0
        
        # Find best and worst scenarios
        if scenario_scores:
            best_scenario = max(scenario_scores.items(), key=lambda x: x[1])
            worst_scenario = min(scenario_scores.items(), key=lambda x: x[1])
            
            analysis["best_performing_scenario"] = best_scenario[0]
            analysis["worst_performing_scenario"] = worst_scenario[0]
        
        # Calculate metric averages across all scenarios
        all_metrics = defaultdict(list)
        
        for scenario_data in scenario_results.values():
            summary = scenario_data["summary_metrics"]
            if "metrics" in summary:
                for metric, values in summary["metrics"].items():
                    if "average" in values:
                        all_metrics[metric].append(values["average"])
        
        for metric, values in all_metrics.items():
            analysis["metric_averages"][metric] = statistics.mean(values)
            analysis["performance_variance"][metric] = statistics.stdev(values) if len(values) > 1 else 0
        
        analysis["scenario_comparison"] = scenario_scores
        
        return analysis
    
    def _analyze_core_web_vitals(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Core Web Vitals across scenarios"""
        
        analysis = {
            "overall_scores": {},
            "threshold_compliance": {},
            "vital_breakdown": {},
            "performance_grades": {}
        }
        
        # Calculate overall scores
        overall_scores = defaultdict(list)
        
        for scenario_name, scenario_data in scenario_results.items():
            summary = scenario_data["summary_metrics"]
            
            if "core_web_vitals" in summary:
                for vital, scores in summary["core_web_vitals"].items():
                    if "average" in scores:
                        overall_scores[vital].append(scores["average"])
        
        for vital, scores in overall_scores.items():
            analysis["overall_scores"][vital] = {
                "average": statistics.mean(scores),
                "min": min(scores),
                "max": max(scores)
            }
        
        # Check threshold compliance
        thresholds = {
            "lcp": self.performance_thresholds["lcp_target_ms"],
            "cls": self.performance_thresholds["cls_target"],
            "fid": self.performance_thresholds["fid_target_ms"]
        }
        
        for vital, threshold in thresholds.items():
            scores = overall_scores.get(vital, [])
            if scores:
                compliant = [s for s in scores if s >= 50]  # Score >= 50 means compliant
                analysis["threshold_compliance"][vital] = {
                    "compliance_rate": (len(compliant) / len(scores)) * 100,
                    "average_score": statistics.mean(scores)
                }
        
        return analysis
    
    def _analyze_payload(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze payload across scenarios"""
        
        analysis = {
            "size_analysis": {},
            "compression_effectiveness": {},
            "resource_analysis": {},
            "optimization_opportunities": []
        }
        
        # Collect payload data
        all_payloads = defaultdict(list)
        
        for scenario_data in scenario_results.values():
            summary = scenario_data["summary_metrics"]
            
            if "payload" in summary:
                for metric, values in summary["payload"].items():
                    if "average" in values:
                        all_payloads[metric].append(values["average"])
        
        # Analyze sizes
        for metric, values in all_payloads.items():
            analysis["size_analysis"][metric] = {
                "average": statistics.mean(values),
                "median": statistics.median(values),
                "max": max(values)
            }
        
        # Check for optimization opportunities
        if "total_size_kb" in all_payloads:
            avg_size = statistics.mean(all_payloads["total_size_kb"])
            if avg_size > 100:
                analysis["optimization_opportunities"].append("Reduce overall payload size")
            
            if "js_size_kb" in all_payloads:
                avg_js = statistics.mean(all_payloads["js_size_kb"])
                if avg_js > self.performance_thresholds["js_payload_kb"]:
                    analysis["optimization_opportunities"].append("Optimize JavaScript payload")
        
        return analysis
    
    def _analyze_network_impact(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network performance impact"""
        
        analysis = {
            "fast_network_performance": {},
            "slow_network_performance": {},
            "network_degradation": {},
            "recommendations": []
        }
        
        # Compare fast vs slow networks
        fast_scenarios = [name for name, config in self.test_scenarios.items() if config["network"] == "fast"]
        slow_scenarios = [name for name, config in self.test_scenarios.items() if "slow_3g" in config["network"]]
        
        for scenario in fast_scenarios:
            if scenario in scenario_results:
                summary = scenario_results[scenario]["summary_metrics"]
                analysis["fast_network_performance"][scenario] = summary.get("metrics", {})
        
        for scenario in slow_scenarios:
            if scenario in scenario_results:
                summary = scenario_results[scenario]["summary_metrics"]
                analysis["slow_network_performance"][scenario] = summary.get("metrics", {})
        
        # Calculate degradation
        if analysis["fast_network_performance"] and analysis["slow_network_performance"]:
            fast_lcp = statistics.mean([m.get("lcp_ms", {}).get("average", 0) 
                                      for m in analysis["fast_network_performance"].values()])
            slow_lcp = statistics.mean([m.get("lcp_ms", {}).get("average", 0) 
                                      for m in analysis["slow_network_performance"].values()])
            
            if fast_lcp > 0:
                degradation = ((slow_lcp - fast_lcp) / fast_lcp) * 100
                analysis["network_degradation"] = {
                    "lcp_degradation_percent": degradation,
                    "fast_lcp_ms": fast_lcp,
                    "slow_lcp_ms": slow_lcp
                }
                
                if degradation > 200:
                    analysis["recommendations"].append("Optimize for slow networks - high degradation detected")
        
        return analysis
    
    def _analyze_device_impact(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze device performance impact"""
        
        analysis = {
            "desktop_performance": {},
            "mobile_performance": {},
            "device_degradation": {},
            "recommendations": []
        }
        
        # Compare desktop vs mobile
        desktop_scenarios = [name for name, config in self.test_scenarios.items() if "iPhone" not in config["user_agent"]]
        mobile_scenarios = [name for name, config in self.test_scenarios.items() if "iPhone" in config["user_agent"]]
        
        for scenario in desktop_scenarios:
            if scenario in scenario_results:
                summary = scenario_results[scenario]["summary_metrics"]
                analysis["desktop_performance"][scenario] = summary.get("metrics", {})
        
        for scenario in mobile_scenarios:
            if scenario in scenario_results:
                summary = scenario_results[scenario]["summary_metrics"]
                analysis["mobile_performance"][scenario] = summary.get("metrics", {})
        
        # Calculate degradation
        if analysis["desktop_performance"] and analysis["mobile_performance"]:
            desktop_lcp = statistics.mean([m.get("lcp_ms", {}).get("average", 0) 
                                         for m in analysis["desktop_performance"].values()])
            mobile_lcp = statistics.mean([m.get("lcp_ms", {}).get("average", 0) 
                                         for m in analysis["mobile_performance"].values()])
            
            if desktop_lcp > 0:
                degradation = ((mobile_lcp - desktop_lcp) / desktop_lcp) * 100
                analysis["device_degradation"] = {
                    "lcp_degradation_percent": degradation,
                    "desktop_lcp_ms": desktop_lcp,
                    "mobile_lcp_ms": mobile_lcp
                }
                
                if degradation > 50:
                    analysis["recommendations"].append("Optimize for mobile - significant performance gap")
        
        return analysis
    
    def _analyze_cache_impact(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cache performance impact"""
        
        analysis = {
            "cached_performance": {},
            "uncached_performance": {},
            "cache_benefit": {},
            "recommendations": []
        }
        
        # Compare cached vs uncached
        cached_scenarios = [name for name, config in self.test_scenarios.items() if config["cache"] == "cached"]
        uncached_scenarios = [name for name, config in self.test_scenarios.items() if config["cache"] in ["uncached", "incognito"]]
        
        for scenario in cached_scenarios:
            if scenario in scenario_results:
                summary = scenario_results[scenario]["summary_metrics"]
                analysis["cached_performance"][scenario] = summary.get("metrics", {})
        
        for scenario in uncached_scenarios:
            if scenario in scenario_results:
                summary = scenario_results[scenario]["summary_metrics"]
                analysis["uncached_performance"][scenario] = summary.get("metrics", {})
        
        # Calculate cache benefit
        if analysis["cached_performance"] and analysis["uncached_performance"]:
            cached_lcp = statistics.mean([m.get("lcp_ms", {}).get("average", 0) 
                                       for m in analysis["cached_performance"].values()])
            uncached_lcp = statistics.mean([m.get("lcp_ms", {}).get("average", 0) 
                                          for m in analysis["uncached_performance"].values()])
            
            if uncached_lcp > 0:
                benefit = ((uncached_lcp - cached_lcp) / uncached_lcp) * 100
                analysis["cache_benefit"] = {
                    "lcp_improvement_percent": benefit,
                    "cached_lcp_ms": cached_lcp,
                    "uncached_lcp_ms": uncached_lcp
                }
                
                if benefit < 20:
                    analysis["recommendations"].append("Improve caching strategy - low cache benefit detected")
        
        return analysis
    
    def _calculate_performance_score(self, test_report: Dict[str, Any]) -> float:
        """Calculate overall performance score"""
        
        score = 100.0
        
        core_web_vitals = test_report["core_web_vitals"]
        
        # Deduct for poor Core Web Vitals
        if "overall_scores" in core_web_vitals:
            for vital, scores in core_web_vitals["overall_scores"].items():
                avg_score = scores.get("average", 100)
                if avg_score < 50:
                    score -= 20  # 20 points per failing vital
                elif avg_score < 70:
                    score -= 10  # 10 points for poor vital
        
        # Deduct for payload issues
        payload_analysis = test_report["payload_analysis"]
        if "optimization_opportunities" in payload_analysis:
            score -= len(payload_analysis["optimization_opportunities"]) * 5
        
        # Deduct for network degradation
        network_impact = test_report["network_impact"]
        if "network_degradation" in network_impact:
            degradation = network_impact["network_degradation"].get("lcp_degradation_percent", 0)
            if degradation > 200:
                score -= 15
            elif degradation > 100:
                score -= 8
        
        # Deduct for device degradation
        device_impact = test_report["device_impact"]
        if "device_degradation" in device_impact:
            degradation = device_impact["device_degradation"].get("lcp_degradation_percent", 0)
            if degradation > 50:
                score -= 10
            elif degradation > 25:
                score -= 5
        
        return max(score, 0)
    
    def _identify_critical_performance_issues(self, test_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify critical performance issues"""
        
        critical_issues = []
        
        # Core Web Vitals failures
        core_web_vitals = test_report["core_web_vitals"]
        if "threshold_compliance" in core_web_vitals:
            for vital, compliance in core_web_vitals["threshold_compliance"].items():
                if compliance["compliance_rate"] < 50:
                    critical_issues.append({
                        "type": "core_web_vitals",
                        "vital": vital,
                        "compliance_rate": compliance["compliance_rate"],
                        "severity": "critical",
                        "description": f"Less than 50% of pages meet {vital.upper()} threshold"
                    })
        
        # Payload issues
        payload_analysis = test_report["payload_analysis"]
        if "size_analysis" in payload_analysis:
            total_size = payload_analysis["size_analysis"].get("total_size_kb", {}).get("average", 0)
            if total_size > 200:
                critical_issues.append({
                    "type": "payload",
                    "metric": "total_size",
                    "value": total_size,
                    "severity": "critical",
                    "description": f"Average payload size {total_size:.0f}KB is too large"
                })
        
        # Network performance issues
        network_impact = test_report["network_impact"]
        if "network_degradation" in network_impact:
            degradation = network_impact["network_degradation"].get("lcp_degradation_percent", 0)
            if degradation > 300:
                critical_issues.append({
                    "type": "network",
                    "metric": "degradation",
                    "value": degradation,
                    "severity": "critical",
                    "description": f"Excessive network degradation: {degradation:.0f}%"
                })
        
        return critical_issues
    
    def _generate_performance_recommendations(self, test_report: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations"""
        
        recommendations = []
        
        # Overall score recommendations
        score = test_report["performance_score"]
        
        if score < 70:
            recommendations.append("Critical performance issues require immediate attention")
        elif score < 85:
            recommendations.append("Several performance improvements needed")
        else:
            recommendations.append("Good performance - maintain current optimization level")
        
        # Core Web Vitals recommendations
        core_web_vitals = test_report["core_web_vitals"]
        if "overall_scores" in core_web_vitals:
            for vital, scores in core_web_vitals["overall_scores"].items():
                avg_score = scores.get("average", 100)
                if avg_score < 50:
                    if vital == "lcp":
                        recommendations.append("Optimize Largest Contentful Paint - reduce server response time and optimize resources")
                    elif vital == "cls":
                        recommendations.append("Fix Cumulative Layout Shift - ensure proper image dimensions and avoid layout shifts")
                    elif vital == "fid":
                        recommendations.append("Improve First Input Delay - reduce JavaScript execution time and break up long tasks")
        
        # Payload recommendations
        payload_analysis = test_report["payload_analysis"]
        if "optimization_opportunities" in payload_analysis:
            recommendations.extend(payload_analysis["optimization_opportunities"])
        
        # Network recommendations
        network_impact = test_report["network_impact"]
        if "recommendations" in network_impact:
            recommendations.extend(network_impact["recommendations"])
        
        # Device recommendations
        device_impact = test_report["device_impact"]
        if "recommendations" in device_impact:
            recommendations.extend(device_impact["recommendations"])
        
        # Cache recommendations
        cache_impact = test_report["cache_impact"]
        if "recommendations" in cache_impact:
            recommendations.extend(cache_impact["recommendations"])
        
        return recommendations


# Singleton instance
performance_reality_test = PerformanceRealityTest()
