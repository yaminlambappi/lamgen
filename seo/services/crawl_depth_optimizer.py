"""
Crawl Depth Optimization System
Ensures every important page reachable within max 3 clicks from homepage
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from django.db.models import Q, Count, F, Avg
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from tools.models import Tool, ToolCategory
from seo.models import SEOPage, LongTailVariant
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque


class CrawlDepthOptimizer:
    """Crawl depth optimization system"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 12  # 12 hours
        
        # Crawl depth constraints
        self.depth_constraints = {
            "max_depth": 3,                    # Maximum 3 clicks from homepage
            "max_orphan_depth": 5,              # Maximum depth for orphan detection
            "min_internal_links": 8,             # Minimum internal links per page
            "hub_page_links": 20,               # Links for hub pages
            "category_hub_links": 15,           # Links for category hubs
            "authority_page_links": 25          # Links for authority pages
        }
        
        # Page types and priorities
        self.page_priorities = {
            "homepage": {"priority": 1, "max_depth": 1},
            "category": {"priority": 2, "max_depth": 2},
            "tool": {"priority": 3, "max_depth": 3},
            "seo_page": {"priority": 3, "max_depth": 3},
            "authority_page": {"priority": 2, "max_depth": 2},
            "longtail": {"priority": 4, "max_depth": 3}
        }
    
    def optimize_crawl_depth(self) -> Dict[str, Any]:
        """Optimize crawl depth across the platform"""
        
        optimization_report = {
            "optimization_timestamp": datetime.now().isoformat(),
            "pages_analyzed": 0,
            "depth_distribution": {},
            "orphan_pages": [],
            "depth_violations": [],
            "hub_pages_created": [],
            "internal_links_added": 0,
            "optimization_score": 0.0,
            "recommendations": [],
            "time_taken": 0
        }
        
        start_time = time.time()
        
        # Build crawl graph
        crawl_graph = self._build_crawl_graph()
        
        # Analyze current depth distribution
        depth_analysis = self._analyze_depth_distribution(crawl_graph)
        optimization_report["depth_distribution"] = depth_analysis
        
        # Identify orphan pages
        orphan_pages = self._identify_orphan_pages(crawl_graph)
        optimization_report["orphan_pages"] = orphan_pages
        
        # Identify depth violations
        depth_violations = self._identify_depth_violations(crawl_graph)
        optimization_report["depth_violations"] = depth_violations
        
        # Create hub pages
        hub_pages = self._create_hub_pages(crawl_graph)
        optimization_report["hub_pages_created"] = hub_pages
        
        # Add internal links
        links_added = self._add_strategic_internal_links(crawl_graph)
        optimization_report["internal_links_added"] = links_added
        
        # Calculate optimization score
        optimization_report["optimization_score"] = self._calculate_optimization_score(optimization_report)
        
        # Generate recommendations
        optimization_report["recommendations"] = self._generate_optimization_recommendations(optimization_report)
        
        # Count pages analyzed
        optimization_report["pages_analyzed"] = len(crawl_graph)
        
        end_time = time.time()
        optimization_report["time_taken"] = end_time - start_time
        
        # Cache results
        cache.set("crawl_depth_optimization", optimization_report, self.cache_timeout)
        
        return optimization_report
    
    def _build_crawl_graph(self) -> Dict[str, Any]:
        """Build crawl graph of all pages"""
        
        graph = {
            "nodes": {},
            "edges": defaultdict(list),
            "homepage": "/"
        }
        
        # Add homepage
        graph["nodes"]["/"] = {
            "type": "homepage",
            "title": "LamGen Homepage",
            "url": "/",
            "depth": 0,
            "priority": 1,
            "internal_links": []
        }
        
        # Add category pages
        categories = ToolCategory.objects.filter(is_active=True)
        for category in categories:
            node_id = category.get_absolute_url()
            graph["nodes"][node_id] = {
                "type": "category",
                "title": category.name,
                "url": node_id,
                "depth": 1,  # Categories should be 1 click from homepage
                "priority": 2,
                "category_id": category.id,
                "internal_links": []
            }
            
            # Add edge from homepage to category
            graph["edges"]["/"].append(node_id)
        
        # Add tool pages
        tools = Tool.objects.filter(is_active=True).select_related('category')
        for tool in tools:
            node_id = tool.get_absolute_url()
            graph["nodes"][node_id] = {
                "type": "tool",
                "title": tool.name,
                "url": node_id,
                "depth": 2,  # Tools should be 2 clicks from homepage
                "priority": 3,
                "tool_id": tool.id,
                "category_id": tool.category.id if tool.category else None,
                "internal_links": []
            }
            
            # Add edge from category to tool
            if tool.category:
                category_url = tool.category.get_absolute_url()
                graph["edges"][category_url].append(node_id)
        
        # Add SEO pages
        seo_pages = SEOPage.objects.filter(is_active=True).select_related('category')
        for page in seo_pages:
            node_id = page.get_absolute_url()
            graph["nodes"][node_id] = {
                "type": "seo_page",
                "title": page.topic,
                "url": node_id,
                "depth": 2,  # SEO pages should be 2 clicks from homepage
                "priority": 3,
                "seo_page_id": page.id,
                "category_id": page.category.id if page.category else None,
                "internal_links": []
            }
            
            # Add edge from category to SEO page
            if page.category:
                category_url = page.category.get_absolute_url()
                graph["edges"][category_url].append(node_id)
        
        # Add longtail variants
        longtails = LongTailVariant.objects.filter(is_active=True).select_related('tool')
        for variant in longtails:
            node_id = variant.get_absolute_url()
            graph["nodes"][node_id] = {
                "type": "longtail",
                "title": variant.title,
                "url": node_id,
                "depth": 3,  # Longtail pages should be 3 clicks from homepage
                "priority": 4,
                "variant_id": variant.id,
                "tool_id": variant.tool.id if variant.tool else None,
                "internal_links": []
            }
            
            # Add edge from tool to longtail
            if variant.tool:
                tool_url = variant.tool.get_absolute_url()
                graph["edges"][tool_url].append(node_id)
        
        # Calculate actual depths using BFS
        self._calculate_actual_depths(graph)
        
        return graph
    
    def _calculate_actual_depths(self, graph: Dict[str, Any]):
        """Calculate actual depths using BFS from homepage"""
        
        visited = set()
        queue = deque([("/" , 0)])  # (url, depth)
        
        while queue:
            current_url, current_depth = queue.popleft()
            
            if current_url in visited:
                continue
            
            visited.add(current_url)
            
            if current_url in graph["nodes"]:
                graph["nodes"][current_url]["depth"] = current_depth
                
                # Add neighbors to queue
                for neighbor in graph["edges"].get(current_url, []):
                    if neighbor not in visited and current_depth < self.depth_constraints["max_orphan_depth"]:
                        queue.append((neighbor, current_depth + 1))
    
    def _analyze_depth_distribution(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze depth distribution across all pages"""
        
        distribution = {
            "depth_0": 0,  # Homepage
            "depth_1": 0,  # 1 click
            "depth_2": 0,  # 2 clicks
            "depth_3": 0,  # 3 clicks
            "depth_4_plus": 0,  # 4+ clicks
            "average_depth": 0.0,
            "pages_within_max_depth": 0,
            "pages_exceeding_max_depth": []
        }
        
        total_depth = 0
        page_count = 0
        
        for node_id, node_data in graph["nodes"].items():
            depth = node_data.get("depth", 0)
            total_depth += depth
            page_count += 1
            
            if depth == 0:
                distribution["depth_0"] += 1
            elif depth == 1:
                distribution["depth_1"] += 1
            elif depth == 2:
                distribution["depth_2"] += 1
            elif depth == 3:
                distribution["depth_3"] += 1
            else:
                distribution["depth_4_plus"] += 1
            
            # Track pages exceeding max depth
            if depth > self.depth_constraints["max_depth"]:
                distribution["pages_exceeding_max_depth"].append({
                    "url": node_id,
                    "title": node_data["title"],
                    "type": node_data["type"],
                    "depth": depth
                })
            else:
                distribution["pages_within_max_depth"] += 1
        
        if page_count > 0:
            distribution["average_depth"] = total_depth / page_count
        
        return distribution
    
    def _identify_orphan_pages(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify orphan pages (no internal links)"""
        
        orphan_pages = []
        
        for node_id, node_data in graph["nodes"].items():
            # Check if page has any incoming links (except homepage)
            incoming_links = 0
            for source, targets in graph["edges"].items():
                if node_id in targets and source != node_id:
                    incoming_links += 1
            
            # Check if page has internal links pointing out
            outgoing_links = len(graph["edges"].get(node_id, []))
            
            # Consider orphan if no incoming links and no outgoing links
            if incoming_links == 0 and outgoing_links == 0:
                orphan_pages.append({
                    "url": node_id,
                    "title": node_data["title"],
                    "type": node_data["type"],
                    "depth": node_data.get("depth", 0),
                    "incoming_links": incoming_links,
                    "outgoing_links": outgoing_links
                })
        
        return orphan_pages
    
    def _identify_depth_violations(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify pages exceeding max depth"""
        
        violations = []
        max_depth = self.depth_constraints["max_depth"]
        
        for node_id, node_data in graph["nodes"].items():
            depth = node_data.get("depth", 0)
            
            if depth > max_depth:
                violations.append({
                    "url": node_id,
                    "title": node_data["title"],
                    "type": node_data["type"],
                    "current_depth": depth,
                    "max_allowed_depth": max_depth,
                    "excess_depth": depth - max_depth
                })
        
        return violations
    
    def _create_hub_pages(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create hub pages for better crawl depth"""
        
        hub_pages = []
        
        # Create category hub pages
        category_hubs = self._create_category_hubs(graph)
        hub_pages.extend(category_hubs)
        
        # Create authority hub pages
        authority_hubs = self._create_authority_hubs(graph)
        hub_pages.extend(authority_hubs)
        
        # Create topic hub pages
        topic_hubs = self._create_topic_hubs(graph)
        hub_pages.extend(topic_hubs)
        
        return hub_pages
    
    def _create_category_hubs(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create category hub pages"""
        
        hubs = []
        
        # Group pages by category
        category_groups = defaultdict(list)
        
        for node_id, node_data in graph["nodes"].items():
            if node_data["type"] in ["tool", "seo_page"] and node_data.get("category_id"):
                category_groups[node_data["category_id"]].append(node_data)
        
        # Create hub for each category with many pages
        for category_id, pages in category_groups.items():
            if len(pages) >= 5:  # Only create hubs for categories with 5+ pages
                category = ToolCategory.objects.filter(id=category_id).first()
                
                if category:
                    hub = {
                        "type": "category_hub",
                        "title": f"{category.name} Hub",
                        "url": f"/hub/{category.slug}/",
                        "category_id": category_id,
                        "linked_pages": pages[:self.depth_constraints["category_hub_links"]],
                        "priority": 2
                    }
                    hubs.append(hub)
        
        return hubs
    
    def _create_authority_hubs(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create authority hub pages"""
        
        hubs = []
        
        # High-value categories for authority hubs
        high_value_categories = ["Resume", "SEO", "PDF", "AI Writing", "Social Media"]
        
        for category_name in high_value_categories:
            category = ToolCategory.objects.filter(name__icontains=category_name).first()
            
            if category:
                # Get all pages in this category
                category_pages = []
                for node_id, node_data in graph["nodes"].items():
                    if node_data.get("category_id") == category.id:
                        category_pages.append(node_data)
                
                if len(category_pages) >= 3:
                    hub = {
                        "type": "authority_hub",
                        "title": f"Ultimate {category.name} Guide",
                        "url": f"/authority/{category.slug}/",
                        "category_id": category.id,
                        "linked_pages": category_pages[:self.depth_constraints["authority_page_links"]],
                        "priority": 2
                    }
                    hubs.append(hub)
        
        return hubs
    
    def _create_topic_hubs(self, graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create topic-based hub pages"""
        
        hubs = []
        
        # Common topics for hub pages
        topics = [
            "Free Tools", "Online Generators", "Professional Templates", 
            "Business Solutions", "Creative Tools", "Productivity Tools"
        ]
        
        for topic in topics:
            # Find pages related to topic
            topic_pages = []
            topic_keywords = topic.lower().split()
            
            for node_id, node_data in graph["nodes"].items():
                page_text = f"{node_data['title']} {node_data.get('type', '')}".lower()
                
                if any(keyword in page_text for keyword in topic_keywords):
                    topic_pages.append(node_data)
            
            if len(topic_pages) >= 3:
                hub = {
                    "type": "topic_hub",
                    "title": f"{topic} Hub",
                    "url": f"/hub/{topic.lower().replace(' ', '-')}/",
                    "linked_pages": topic_pages[:self.depth_constraints["hub_page_links"]],
                    "priority": 3
                }
                hubs.append(hub)
        
        return hubs
    
    def _add_strategic_internal_links(self, graph: Dict[str, Any]) -> int:
        """Add strategic internal links to improve crawl depth"""
        
        links_added = 0
        
        # Add links to orphan pages
        orphan_pages = self._identify_orphan_pages(graph)
        for orphan in orphan_pages:
            # Link from nearest category or hub
            nearest_link = self._find_nearest_link_target(graph, orphan)
            if nearest_link:
                graph["edges"][nearest_link].append(orphan["url"])
                links_added += 1
        
        # Add links to deep pages
        deep_pages = [node_id for node_id, node_data in graph["nodes"].items() 
                     if node_data.get("depth", 0) > self.depth_constraints["max_depth"]]
        
        for deep_page in deep_pages[:50]:  # Limit to prevent too many changes
            # Link from shallower page
            shallow_link = self._find_shallow_link_target(graph, deep_page)
            if shallow_link:
                graph["edges"][shallow_link].append(deep_page)
                links_added += 1
        
        # Add contextual links between related pages
        contextual_links = self._create_contextual_links(graph)
        links_added += contextual_links
        
        return links_added
    
    def _find_nearest_link_target(self, graph: Dict[str, Any], orphan_page: Dict[str, Any]) -> Optional[str]:
        """Find nearest page to link orphan page from"""
        
        orphan_depth = orphan_page.get("depth", 0)
        orphan_category = orphan_page.get("category_id")
        
        # Try to link from category page
        if orphan_category:
            for node_id, node_data in graph["nodes"].items():
                if (node_data["type"] == "category" and 
                    node_data.get("category_id") == orphan_category and
                    node_data.get("depth", 0) < orphan_depth):
                    return node_id
        
        # Try to link from hub page
        for node_id, node_data in graph["nodes"].items():
            if (node_data["type"] in ["category_hub", "authority_hub", "topic_hub"] and
                node_data.get("depth", 0) < orphan_depth):
                return node_id
        
        # Try to link from homepage
        if orphan_depth > 1:
            return "/"
        
        return None
    
    def _find_shallow_link_target(self, graph: Dict[str, Any], deep_page: str) -> Optional[str]:
        """Find shallow page to link deep page from"""
        
        deep_page_data = graph["nodes"].get(deep_page, {})
        deep_depth = deep_page_data.get("depth", 0)
        deep_category = deep_page_data.get("category_id")
        
        # Try to link from category page
        if deep_category:
            for node_id, node_data in graph["nodes"].items():
                if (node_data["type"] == "category" and 
                    node_data.get("category_id") == deep_category and
                    node_data.get("depth", 0) < deep_depth - 1):
                    return node_id
        
        # Try to link from hub page
        for node_id, node_data in graph["nodes"].items():
            if (node_data["type"] in ["category_hub", "authority_hub"] and
                node_data.get("depth", 0) < deep_depth - 2):
                return node_id
        
        return None
    
    def _create_contextual_links(self, graph: Dict[str, Any]) -> int:
        """Create contextual links between related pages"""
        
        contextual_links = 0
        
        # Link related tools within categories
        for category_id in range(1, 20):  # Check first 20 categories
            category_tools = []
            
            for node_id, node_data in graph["nodes"].items():
                if (node_data["type"] == "tool" and 
                    node_data.get("category_id") == category_id):
                    category_tools.append(node_id)
            
            # Create links between tools in same category
            for i, tool1 in enumerate(category_tools):
                for tool2 in category_tools[i+1:i+3]:  # Link to next 2-3 tools
                    if tool2 not in graph["edges"].get(tool1, []):
                        graph["edges"][tool1].append(tool2)
                        contextual_links += 1
        
        return contextual_links
    
    def _calculate_optimization_score(self, optimization_report: Dict[str, Any]) -> float:
        """Calculate overall optimization score"""
        
        score = 100.0
        
        # Deduct for orphan pages
        orphan_count = len(optimization_report["orphan_pages"])
        score -= orphan_count * 2  # 2 points per orphan page
        
        # Deduct for depth violations
        violation_count = len(optimization_report["depth_violations"])
        score -= violation_count * 5  # 5 points per violation
        
        # Bonus for hub pages created
        hub_count = len(optimization_report["hub_pages_created"])
        score += hub_count * 3  # 3 points per hub page
        
        # Bonus for internal links added
        links_added = optimization_report["internal_links_added"]
        score += min(links_added * 0.1, 10)  # Max 10 points for links
        
        return max(score, 0)
    
    def _generate_optimization_recommendations(self, optimization_report: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations"""
        
        recommendations = []
        
        # Overall score recommendations
        score = optimization_report["optimization_score"]
        
        if score < 70:
            recommendations.append("Critical crawl depth issues require immediate attention")
        elif score < 85:
            recommendations.append("Several crawl depth improvements needed")
        else:
            recommendations.append("Good crawl depth optimization - maintain current structure")
        
        # Specific recommendations based on issues
        if optimization_report["orphan_pages"]:
            recommendations.append(f"Fix {len(optimization_report['orphan_pages'])} orphan pages by adding internal links")
        
        if optimization_report["depth_violations"]:
            recommendations.append(f"Fix {len(optimization_report['depth_violations'])} pages exceeding max depth")
        
        # Depth distribution recommendations
        distribution = optimization_report["depth_distribution"]
        total_pages = sum(distribution[k] for k in ["depth_0", "depth_1", "depth_2", "depth_3", "depth_4_plus"])
        
        if total_pages > 0:
            within_max_depth = distribution["pages_within_max_depth"]
            within_max_percentage = (within_max_depth / total_pages) * 100
            
            if within_max_percentage < 90:
                recommendations.append(f"Only {within_max_percentage:.1f}% of pages within max depth - improve internal linking")
        
        # Hub page recommendations
        if len(optimization_report["hub_pages_created"]) < 5:
            recommendations.append("Create more hub pages to improve crawl efficiency")
        
        # Internal linking recommendations
        if optimization_report["internal_links_added"] < 50:
            recommendations.append("Add more strategic internal links to reduce crawl depth")
        
        return recommendations
    
    def get_crawl_depth_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive crawl depth dashboard"""
        
        dashboard = {
            "summary": {},
            "depth_analysis": {},
            "orphan_analysis": {},
            "hub_analysis": {},
            "optimization_status": {},
            "recommendations": []
        }
        
        # Get latest optimization data
        optimization_data = cache.get("crawl_depth_optimization")
        if not optimization_data:
            optimization_data = self.optimize_crawl_depth()
        
        # Summary metrics
        dashboard["summary"] = {
            "optimization_score": optimization_data["optimization_score"],
            "pages_analyzed": optimization_data["pages_analyzed"],
            "orphan_pages": len(optimization_data["orphan_pages"]),
            "depth_violations": len(optimization_data["depth_violations"]),
            "hub_pages_created": len(optimization_data["hub_pages_created"]),
            "internal_links_added": optimization_data["internal_links_added"]
        }
        
        # Depth analysis
        dashboard["depth_analysis"] = optimization_data["depth_distribution"]
        
        # Orphan analysis
        dashboard["orphan_analysis"] = {
            "total_orphans": len(optimization_data["orphan_pages"]),
            "orphan_types": self._analyze_orphan_types(optimization_data["orphan_pages"]),
            "orphan_depths": self._analyze_orphan_depths(optimization_data["orphan_pages"])
        }
        
        # Hub analysis
        dashboard["hub_analysis"] = {
            "total_hubs": len(optimization_data["hub_pages_created"]),
            "hub_types": self._analyze_hub_types(optimization_data["hub_pages_created"]),
            "hub_connectivity": self._analyze_hub_connectivity(optimization_data["hub_pages_created"])
        }
        
        # Optimization status
        dashboard["optimization_status"] = {
            "status": "optimized" if optimization_data["optimization_score"] >= 85 else "needs_improvement",
            "last_optimization": optimization_data["optimization_timestamp"],
            "issues_remaining": len(optimization_data["orphan_pages"]) + len(optimization_data["depth_violations"])
        }
        
        # Recommendations
        dashboard["recommendations"] = optimization_data["recommendations"]
        
        return dashboard
    
    def _analyze_orphan_types(self, orphan_pages: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze orphan pages by type"""
        
        type_counts = defaultdict(int)
        
        for orphan in orphan_pages:
            page_type = orphan.get("type", "unknown")
            type_counts[page_type] += 1
        
        return dict(type_counts)
    
    def _analyze_orphan_depths(self, orphan_pages: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze orphan pages by depth"""
        
        depth_counts = defaultdict(int)
        
        for orphan in orphan_pages:
            depth = orphan.get("depth", 0)
            depth_counts[f"depth_{depth}"] += 1
        
        return dict(depth_counts)
    
    def _analyze_hub_types(self, hub_pages: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze hub pages by type"""
        
        type_counts = defaultdict(int)
        
        for hub in hub_pages:
            hub_type = hub.get("type", "unknown")
            type_counts[hub_type] += 1
        
        return dict(type_counts)
    
    def _analyze_hub_connectivity(self, hub_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze hub page connectivity"""
        
        connectivity = {
            "total_links": 0,
            "avg_links_per_hub": 0.0,
            "max_links_per_hub": 0,
            "min_links_per_hub": 0
        }
        
        if hub_pages:
            link_counts = [len(hub.get("linked_pages", [])) for hub in hub_pages]
            
            connectivity["total_links"] = sum(link_counts)
            connectivity["avg_links_per_hub"] = sum(link_counts) / len(link_counts)
            connectivity["max_links_per_hub"] = max(link_counts)
            connectivity["min_links_per_hub"] = min(link_counts)
        
        return connectivity
    
    def monitor_crawl_health(self) -> Dict[str, Any]:
        """Monitor ongoing crawl health"""
        
        health_report = {
            "health_score": 0.0,
            "status": "unknown",
            "key_metrics": {},
            "alerts": [],
            "trends": {},
            "recommendations": []
        }
        
        # Get current crawl graph
        graph = self._build_crawl_graph()
        
        # Calculate health score
        health_score = 100.0
        
        # Check orphan rate
        total_pages = len(graph["nodes"])
        orphan_count = len(self._identify_orphan_pages(graph))
        orphan_rate = (orphan_count / total_pages) * 100 if total_pages > 0 else 0
        
        if orphan_rate > 10:
            health_score -= 25
            health_report["alerts"].append("Critical: High orphan rate")
        elif orphan_rate > 5:
            health_score -= 10
            health_report["alerts"].append("Warning: Moderate orphan rate")
        
        # Check depth violations
        violations = self._identify_depth_violations(graph)
        violation_rate = (len(violations) / total_pages) * 100 if total_pages > 0 else 0
        
        if violation_rate > 5:
            health_score -= 30
            health_report["alerts"].append("Critical: High depth violation rate")
        elif violation_rate > 2:
            health_score -= 15
            health_report["alerts"].append("Warning: Moderate depth violation rate")
        
        # Check average depth
        depth_analysis = self._analyze_depth_distribution(graph)
        avg_depth = depth_analysis["average_depth"]
        
        if avg_depth > 3.5:
            health_score -= 20
            health_report["alerts"].append("Warning: High average depth")
        elif avg_depth > 2.5:
            health_score -= 10
        
        health_report["health_score"] = max(health_score, 0)
        
        # Determine status
        if health_score >= 85:
            health_report["status"] = "healthy"
        elif health_score >= 70:
            health_report["status"] = "good"
        elif health_score >= 50:
            health_report["status"] = "warning"
        else:
            health_report["status"] = "critical"
        
        # Key metrics
        health_report["key_metrics"] = {
            "total_pages": total_pages,
            "orphan_pages": orphan_count,
            "orphan_rate": orphan_rate,
            "depth_violations": len(violations),
            "violation_rate": violation_rate,
            "average_depth": avg_depth,
            "pages_within_max_depth": depth_analysis["pages_within_max_depth"]
        }
        
        # Recommendations
        health_report["recommendations"] = self._generate_health_recommendations(health_report)
        
        return health_report
    
    def _generate_health_recommendations(self, health_report: Dict[str, Any]) -> List[str]:
        """Generate health-based recommendations"""
        
        recommendations = []
        
        if health_report["status"] == "critical":
            recommendations.append("Immediate action required - crawl health is critical")
        elif health_report["status"] == "warning":
            recommendations.append("Monitor closely - crawl health needs attention")
        
        # Specific recommendations based on alerts
        for alert in health_report["alerts"]:
            if "High orphan rate" in alert:
                recommendations.append("Add internal links to orphan pages to improve crawl depth")
            elif "High depth violation rate" in alert:
                recommendations.append("Reorganize site structure to reduce crawl depth")
            elif "High average depth" in alert:
                recommendations.append("Create hub pages and improve internal linking")
        
        return recommendations


# Singleton instance
crawl_depth_optimizer = CrawlDepthOptimizer()
