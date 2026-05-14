"""
Massive Internal Link Graph Analysis
Ensures every page connected, no isolated clusters, balanced authority distribution
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from django.db.models import Q, Count, F, Avg
from django.core.cache import cache
from django.conf import settings
from apps.tools.models import Tool, ToolCategory
from apps.seo.models import SEOPage, LongTailVariant
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
import networkx as nx


class InternalLinkGraph:
    """Massive internal link graph analysis system"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 12  # 12 hours
        
        # Graph analysis thresholds
        self.graph_thresholds = {
            "min_page_authority": 10,          # Minimum authority score
            "max_isolated_cluster_size": 5,     # Maximum isolated cluster size
            "min_hub_connections": 15,          # Minimum connections for hub pages
            "authority_distribution_variance": 0.3, # Max variance in authority distribution
            "max_orphan_pages": 10,             # Maximum orphan pages allowed
            "min_graph_density": 0.05,          # Minimum graph density
            "max_centrality_variance": 0.4      # Max variance in centrality scores
        }
        
        # Link types and weights
        self.link_weights = {
            "contextual": 1.0,      # Contextual links have highest weight
            "navigational": 0.8,    # Navigation links
            "related": 0.9,         # Related content links
            "authority": 1.2,        # Authority page links
            "category": 0.7,        # Category links
            "cross_category": 0.6   # Cross-category links
        }
    
    def analyze_internal_link_graph(self) -> Dict[str, Any]:
        """Comprehensive internal link graph analysis"""
        
        analysis_report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "graph_metrics": {},
            "connectivity_analysis": {},
            "authority_distribution": {},
            "isolated_clusters": [],
            "orphan_pages": [],
            "hub_pages": [],
            "weak_clusters": [],
            "optimization_score": 0.0,
            "recommendations": [],
            "time_taken": 0
        }
        
        start_time = time.time()
        
        # Build internal link graph
        graph = self._build_link_graph()
        
        # Calculate graph metrics
        graph_metrics = self._calculate_graph_metrics(graph)
        analysis_report["graph_metrics"] = graph_metrics
        
        # Analyze connectivity
        connectivity = self._analyze_connectivity(graph)
        analysis_report["connectivity_analysis"] = connectivity
        
        # Analyze authority distribution
        authority_dist = self._analyze_authority_distribution(graph)
        analysis_report["authority_distribution"] = authority_dist
        
        # Identify isolated clusters
        isolated_clusters = self._identify_isolated_clusters(graph)
        analysis_report["isolated_clusters"] = isolated_clusters
        
        # Identify orphan pages
        orphan_pages = self._identify_orphan_pages(graph)
        analysis_report["orphan_pages"] = orphan_pages
        
        # Identify hub pages
        hub_pages = self._identify_hub_pages(graph)
        analysis_report["hub_pages"] = hub_pages
        
        # Identify weak clusters
        weak_clusters = self._identify_weak_clusters(graph)
        analysis_report["weak_clusters"] = weak_clusters
        
        # Calculate optimization score
        analysis_report["optimization_score"] = self._calculate_optimization_score(analysis_report)
        
        # Generate recommendations
        analysis_report["recommendations"] = self._generate_graph_recommendations(analysis_report)
        
        end_time = time.time()
        analysis_report["time_taken"] = end_time - start_time
        
        # Cache results
        cache.set("internal_link_graph_analysis", analysis_report, self.cache_timeout)
        
        return analysis_report
    
    def _build_link_graph(self) -> nx.DiGraph:
        """Build directed internal link graph"""
        
        graph = nx.DiGraph()
        
        # Add all pages as nodes
        pages_data = self._get_all_pages_data()
        
        for page_data in pages_data:
            graph.add_node(page_data["url"], **page_data)
        
        # Add internal links as edges
        for page_data in pages_data:
            source_url = page_data["url"]
            internal_links = page_data.get("internal_links", [])
            
            for link_data in internal_links:
                target_url = link_data.get("url")
                link_type = link_data.get("type", "contextual")
                link_weight = self.link_weights.get(link_type, 1.0)
                
                if target_url in graph.nodes:
                    graph.add_edge(source_url, target_url, 
                                 weight=link_weight, 
                                 type=link_type)
        
        return graph
    
    def _get_all_pages_data(self) -> List[Dict[str, Any]]:
        """Get data for all pages"""
        
        pages = []
        
        # Add tools
        tools = Tool.objects.filter(is_active=True).select_related('category')
        for tool in tools:
            # Generate internal links for tool
            internal_links = self._generate_tool_internal_links(tool)
            
            pages.append({
                "url": tool.get_absolute_url(),
                "title": tool.name,
                "type": "tool",
                "category_id": tool.category.id if tool.category else None,
                "priority": 3,
                "authority_score": self._calculate_initial_authority(tool),
                "internal_links": internal_links
            })
        
        # Add SEO pages
        seo_pages = SEOPage.objects.filter(is_active=True).select_related('category')
        for page in seo_pages:
            internal_links = self._generate_seo_page_internal_links(page)
            
            pages.append({
                "url": page.get_absolute_url(),
                "title": page.topic,
                "type": "seo_page",
                "category_id": page.category.id if page.category else None,
                "priority": 3,
                "authority_score": self._calculate_seo_page_authority(page),
                "internal_links": internal_links
            })
        
        # Add categories
        categories = ToolCategory.objects.filter(is_active=True)
        for category in categories:
            internal_links = self._generate_category_internal_links(category)
            
            pages.append({
                "url": category.get_absolute_url(),
                "title": category.name,
                "type": "category",
                "category_id": category.id,
                "priority": 2,
                "authority_score": self._calculate_category_authority(category),
                "internal_links": internal_links
            })
        
        # Add longtail variants
        longtails = LongTailVariant.objects.filter(is_active=True).select_related('tool')
        for variant in longtails:
            internal_links = self._generate_longtail_internal_links(variant)
            
            pages.append({
                "url": variant.get_absolute_url(),
                "title": variant.title,
                "type": "longtail",
                "category_id": variant.tool.category.id if variant.tool and variant.tool.category else None,
                "priority": 4,
                "authority_score": self._calculate_longtail_authority(variant),
                "internal_links": internal_links
            })
        
        return pages
    
    def _generate_tool_internal_links(self, tool: Tool) -> List[Dict[str, Any]]:
        """Generate internal links for tool page"""
        
        links = []
        
        # Link to category
        if tool.category:
            links.append({
                "url": tool.category.get_absolute_url(),
                "type": "category",
                "anchor": tool.category.name
            })
        
        # Link to related tools in same category
        related_tools = Tool.objects.filter(
            category=tool.category,
            is_active=True
        ).exclude(id=tool.id).order_by('?')[:5]
        
        for related_tool in related_tools:
            links.append({
                "url": related_tool.get_absolute_url(),
                "type": "related",
                "anchor": related_tool.name
            })
        
        # Link to authority pages
        authority_pages = SEOPage.objects.filter(
            category=tool.category,
            is_active=True,
            topic__icontains="guide"
        )[:3]
        
        for authority_page in authority_pages:
            links.append({
                "url": authority_page.get_absolute_url(),
                "type": "authority",
                "anchor": authority_page.topic
            })
        
        return links
    
    def _generate_seo_page_internal_links(self, page: SEOPage) -> List[Dict[str, Any]]:
        """Generate internal links for SEO page"""
        
        links = []
        
        # Link to category
        if page.category:
            links.append({
                "url": page.category.get_absolute_url(),
                "type": "category",
                "anchor": page.category.name
            })
        
        # Link to tools in same category
        tools = Tool.objects.filter(
            category=page.category,
            is_active=True
        ).order_by('?')[:8]
        
        for tool in tools:
            links.append({
                "url": tool.get_absolute_url(),
                "type": "contextual",
                "anchor": tool.name
            })
        
        return links
    
    def _generate_category_internal_links(self, category: ToolCategory) -> List[Dict[str, Any]]:
        """Generate internal links for category page"""
        
        links = []
        
        # Link to tools in category
        tools = Tool.objects.filter(
            category=category,
            is_active=True
        ).order_by('?')[:15]
        
        for tool in tools:
            links.append({
                "url": tool.get_absolute_url(),
                "type": "navigational",
                "anchor": tool.name
            })
        
        # Link to SEO pages in category
        seo_pages = SEOPage.objects.filter(
            category=category,
            is_active=True
        ).order_by('?')[:5]
        
        for seo_page in seo_pages:
            links.append({
                "url": seo_page.get_absolute_url(),
                "type": "navigational",
                "anchor": seo_page.topic
            })
        
        # Link to related categories
        related_categories = ToolCategory.objects.filter(
            is_active=True
        ).exclude(id=category.id).order_by('?')[:3]
        
        for related_category in related_categories:
            links.append({
                "url": related_category.get_absolute_url(),
                "type": "cross_category",
                "anchor": related_category.name
            })
        
        return links
    
    def _generate_longtail_internal_links(self, variant: LongTailVariant) -> List[Dict[str, Any]]:
        """Generate internal links for longtail variant"""
        
        links = []
        
        # Link to parent tool
        if variant.tool:
            links.append({
                "url": variant.tool.get_absolute_url(),
                "type": "contextual",
                "anchor": variant.tool.name
            })
        
        # Link to category
        if variant.tool and variant.tool.category:
            links.append({
                "url": variant.tool.category.get_absolute_url(),
                "type": "category",
                "anchor": variant.tool.category.name
            })
        
        # Link to related longtails
        related_variants = LongTailVariant.objects.filter(
            tool=variant.tool,
            is_active=True
        ).exclude(id=variant.id).order_by('?')[:3]
        
        for related_variant in related_variants:
            links.append({
                "url": related_variant.get_absolute_url(),
                "type": "related",
                "anchor": related_variant.title
            })
        
        return links
    
    def _calculate_initial_authority(self, tool: Tool) -> float:
        """Calculate initial authority score for tool"""
        
        authority = 10.0  # Base authority
        
        # Add for view count
        if tool.view_count:
            authority += min(tool.view_count / 1000, 20)  # Max 20 points for views
        
        # Add for featured status
        if tool.is_featured:
            authority += 15
        
        # Add for content quality
        if tool.seo_intro:
            authority += 5
        if tool.use_cases:
            authority += 5
        if tool.faq_items:
            authority += 5
        
        # Add for category authority
        if tool.category:
            category_authority = self._calculate_category_authority(tool.category)
            authority += category_authority * 0.3  # 30% of category authority
        
        return authority
    
    def _calculate_seo_page_authority(self, page: SEOPage) -> float:
        """Calculate authority score for SEO page"""
        
        authority = 15.0  # Base authority (higher than tools)
        
        # Add for content length
        if page.content_intro:
            authority += min(len(page.content_intro.split()) / 100, 10)
        
        # Add for category authority
        if page.category:
            category_authority = self._calculate_category_authority(page.category)
            authority += category_authority * 0.4  # 40% of category authority
        
        return authority
    
    def _calculate_category_authority(self, category: ToolCategory) -> float:
        """Calculate authority score for category"""
        
        authority = 20.0  # Base authority (highest)
        
        # Add for number of tools
        tool_count = Tool.objects.filter(category=category, is_active=True).count()
        authority += min(tool_count * 2, 30)  # Max 30 points for tools
        
        # Add for SEO pages
        seo_count = SEOPage.objects.filter(category=category, is_active=True).count()
        authority += min(seo_count * 3, 15)  # Max 15 points for SEO pages
        
        return authority
    
    def _calculate_longtail_authority(self, variant: LongTailVariant) -> float:
        """Calculate authority score for longtail variant"""
        
        authority = 5.0  # Base authority (lowest)
        
        # Add for parent tool authority
        if variant.tool:
            tool_authority = self._calculate_initial_authority(variant.tool)
            authority += tool_authority * 0.2  # 20% of parent tool authority
        
        return authority
    
    def _calculate_graph_metrics(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Calculate comprehensive graph metrics"""
        
        metrics = {
            "total_nodes": graph.number_of_nodes(),
            "total_edges": graph.number_of_edges(),
            "density": 0.0,
            "average_clustering": 0.0,
            "average_path_length": 0.0,
            "diameter": 0,
            "strongly_connected_components": 0,
            "weakly_connected_components": 0,
            "reciprocity": 0.0,
            "assortativity": 0.0
        }
        
        if graph.number_of_nodes() > 0:
            # Basic metrics
            metrics["density"] = nx.density(graph)
            
            # Clustering coefficient
            if graph.number_of_nodes() > 2:
                metrics["average_clustering"] = nx.average_clustering(graph.to_undirected())
            
            # Path length and diameter (for largest component)
            if nx.is_weakly_connected(graph):
                metrics["average_path_length"] = nx.average_shortest_path_length(graph.to_undirected())
                metrics["diameter"] = nx.diameter(graph.to_undirected())
            
            # Connected components
            metrics["strongly_connected_components"] = nx.number_strongly_connected_components(graph)
            metrics["weakly_connected_components"] = nx.number_weakly_connected_components(graph)
            
            # Reciprocity
            metrics["reciprocity"] = nx.reciprocity(graph)
            
            # Assortativity
            if graph.number_of_edges() > 0:
                try:
                    metrics["assortativity"] = nx.degree_assortativity_coefficient(graph)
                except:
                    metrics["assortativity"] = 0.0
        
        return metrics
    
    def _analyze_connectivity(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Analyze graph connectivity"""
        
        connectivity = {
            "is_strongly_connected": nx.is_strongly_connected(graph),
            "is_weakly_connected": nx.is_weakly_connected(graph),
            "largest_component_size": 0,
            "connectivity_ratio": 0.0,
            "bridge_edges": [],
            "articulation_points": [],
            "centrality_scores": {}
        }
        
        # Find largest component
        if not nx.is_weakly_connected(graph):
            components = list(nx.weakly_connected_components(graph))
            largest_component = max(components, key=len)
            connectivity["largest_component_size"] = len(largest_component)
            connectivity["connectivity_ratio"] = len(largest_component) / graph.number_of_nodes()
        else:
            connectivity["largest_component_size"] = graph.number_of_nodes()
            connectivity["connectivity_ratio"] = 1.0
        
        # Find bridge edges (in undirected version)
        undirected_graph = graph.to_undirected()
        bridges = list(nx.bridges(undirected_graph))
        connectivity["bridge_edges"] = bridges
        
        # Find articulation points
        articulation_points = list(nx.articulation_points(undirected_graph))
        connectivity["articulation_points"] = articulation_points
        
        # Calculate centrality scores
        centrality_scores = {
            "degree_centrality": nx.degree_centrality(graph),
            "betweenness_centrality": nx.betweenness_centrality(graph),
            "closeness_centrality": nx.closeness_centrality(graph),
            "pagerank": nx.pagerank(graph)
        }
        connectivity["centrality_scores"] = centrality_scores
        
        return connectivity
    
    def _analyze_authority_distribution(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Analyze authority distribution across pages"""
        
        authority_dist = {
            "average_authority": 0.0,
            "authority_variance": 0.0,
            "authority_range": {"min": 0.0, "max": 0.0},
            "authority_quartiles": {},
            "low_authority_pages": [],
            "high_authority_pages": [],
            "authority_distribution": {}
        }
        
        # Extract authority scores
        authority_scores = []
        for node, data in graph.nodes(data=True):
            authority = data.get("authority_score", 0.0)
            authority_scores.append(authority)
        
        if authority_scores:
            # Calculate statistics
            authority_dist["average_authority"] = sum(authority_scores) / len(authority_scores)
            authority_dist["authority_variance"] = self._calculate_variance(authority_scores)
            authority_dist["authority_range"]["min"] = min(authority_scores)
            authority_dist["authority_range"]["max"] = max(authority_scores)
            
            # Calculate quartiles
            sorted_scores = sorted(authority_scores)
            n = len(sorted_scores)
            authority_dist["authority_quartiles"] = {
                "q1": sorted_scores[n // 4],
                "median": sorted_scores[n // 2],
                "q3": sorted_scores[3 * n // 4]
            }
            
            # Identify low and high authority pages
            q1 = authority_dist["authority_quartiles"]["q1"]
            q3 = authority_dist["authority_quartiles"]["q3"]
            
            for node, data in graph.nodes(data=True):
                authority = data.get("authority_score", 0.0)
                if authority < q1:
                    authority_dist["low_authority_pages"].append({
                        "url": node,
                        "title": data.get("title", ""),
                        "authority": authority
                    })
                elif authority > q3:
                    authority_dist["high_authority_pages"].append({
                        "url": node,
                        "title": data.get("title", ""),
                        "authority": authority
                    })
        
        return authority_dist
    
    def _identify_isolated_clusters(self, graph: nx.DiGraph) -> List[Dict[str, Any]]:
        """Identify isolated clusters"""
        
        isolated_clusters = []
        
        if nx.is_weakly_connected(graph):
            return isolated_clusters  # No isolated clusters if fully connected
        
        # Find weakly connected components
        components = list(nx.weakly_connected_components(graph))
        
        for component in components:
            if len(component) <= self.graph_thresholds["max_isolated_cluster_size"]:
                cluster_data = {
                    "size": len(component),
                    "nodes": [],
                    "isolation_score": 0.0
                }
                
                # Get node data
                for node in component:
                    node_data = graph.nodes.get(node, {})
                    cluster_data["nodes"].append({
                        "url": node,
                        "title": node_data.get("title", ""),
                        "type": node_data.get("type", ""),
                        "authority": node_data.get("authority_score", 0.0)
                    })
                
                # Calculate isolation score (inverse of connections to main component)
                cluster_data["isolation_score"] = 1.0 - (len(component) / graph.number_of_nodes())
                
                isolated_clusters.append(cluster_data)
        
        return isolated_clusters
    
    def _identify_orphan_pages(self, graph: nx.DiGraph) -> List[Dict[str, Any]]:
        """Identify orphan pages (no incoming links)"""
        
        orphan_pages = []
        
        for node in graph.nodes():
            incoming_links = graph.in_degree(node)
            
            if incoming_links == 0:
                node_data = graph.nodes.get(node, {})
                orphan_pages.append({
                    "url": node,
                    "title": node_data.get("title", ""),
                    "type": node_data.get("type", ""),
                    "authority": node_data.get("authority_score", 0.0),
                    "outgoing_links": graph.out_degree(node)
                })
        
        return orphan_pages
    
    def _identify_hub_pages(self, graph: nx.DiGraph) -> List[Dict[str, Any]]:
        """Identify hub pages (high connectivity)"""
        
        hub_pages = []
        
        # Calculate degree centrality
        degree_centrality = nx.degree_centrality(graph)
        
        # Sort by centrality
        sorted_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
        
        # Top 20% as potential hubs
        hub_count = max(1, int(len(sorted_nodes) * 0.2))
        
        for node, centrality in sorted_nodes[:hub_count]:
            if centrality > 0.1:  # Minimum centrality threshold
                node_data = graph.nodes.get(node, {})
                hub_pages.append({
                    "url": node,
                    "title": node_data.get("title", ""),
                    "type": node_data.get("type", ""),
                    "authority": node_data.get("authority_score", 0.0),
                    "centrality": centrality,
                    "in_degree": graph.in_degree(node),
                    "out_degree": graph.out_degree(node),
                    "total_degree": graph.degree(node)
                })
        
        return hub_pages
    
    def _identify_weak_clusters(self, graph: nx.DiGraph) -> List[Dict[str, Any]]:
        """Identify weak clusters (low internal connectivity)"""
        
        weak_clusters = []
        
        # Find communities using modularity
        communities = nx.community.greedy_modularity_communities(graph.to_undirected())
        
        for community in communities:
            if len(community) >= 3:  # Only consider clusters with 3+ nodes
                # Calculate internal density
                subgraph = graph.subgraph(community)
                internal_density = nx.density(subgraph)
                
                # Calculate external connections
                external_connections = 0
                for node in community:
                    external_connections += sum(1 for neighbor in graph.neighbors(node) 
                                           if neighbor not in community)
                
                # Weak cluster if low internal density or few external connections
                if (internal_density < 0.1 or 
                    external_connections < len(community) * 2):
                    
                    cluster_data = {
                        "size": len(community),
                        "internal_density": internal_density,
                        "external_connections": external_connections,
                        "nodes": [],
                        "weakness_score": 0.0
                    }
                    
                    # Get node data
                    for node in community:
                        node_data = graph.nodes.get(node, {})
                        cluster_data["nodes"].append({
                            "url": node,
                            "title": node_data.get("title", ""),
                            "type": node_data.get("type", ""),
                            "authority": node_data.get("authority_score", 0.0)
                        })
                    
                    # Calculate weakness score
                    cluster_data["weakness_score"] = (1.0 - internal_density) * 0.5 + \
                                                  (1.0 - external_connections / (len(community) * 10)) * 0.5
                    
                    weak_clusters.append(cluster_data)
        
        return weak_clusters
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values"""
        
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def _calculate_optimization_score(self, analysis_report: Dict[str, Any]) -> float:
        """Calculate overall optimization score"""
        
        score = 100.0
        
        # Deduct for orphan pages
        orphan_count = len(analysis_report["orphan_pages"])
        score -= orphan_count * 3  # 3 points per orphan page
        
        # Deduct for isolated clusters
        cluster_count = len(analysis_report["isolated_clusters"])
        score -= cluster_count * 10  # 10 points per isolated cluster
        
        # Deduct for weak clusters
        weak_count = len(analysis_report["weak_clusters"])
        score -= weak_count * 5  # 5 points per weak cluster
        
        # Check authority distribution
        authority_variance = analysis_report["authority_distribution"]["authority_variance"]
        if authority_variance > self.graph_thresholds["authority_distribution_variance"]:
            score -= 15  # 15 points for poor authority distribution
        
        # Check graph density
        graph_density = analysis_report["graph_metrics"]["density"]
        if graph_density < self.graph_thresholds["min_graph_density"]:
            score -= 10  # 10 points for low density
        
        # Bonus for good connectivity
        connectivity_ratio = analysis_report["connectivity_analysis"]["connectivity_ratio"]
        if connectivity_ratio >= 0.95:
            score += 10  # 10 points bonus for excellent connectivity
        
        # Bonus for hub pages
        hub_count = len(analysis_report["hub_pages"])
        if hub_count >= 10:
            score += 5  # 5 points bonus for sufficient hubs
        
        return max(score, 0)
    
    def _generate_graph_recommendations(self, analysis_report: Dict[str, Any]) -> List[str]:
        """Generate graph optimization recommendations"""
        
        recommendations = []
        
        # Overall score recommendations
        score = analysis_report["optimization_score"]
        
        if score < 70:
            recommendations.append("Critical internal linking issues require immediate attention")
        elif score < 85:
            recommendations.append("Several internal linking improvements needed")
        else:
            recommendations.append("Good internal linking structure - maintain current strategy")
        
        # Specific recommendations based on issues
        if analysis_report["orphan_pages"]:
            recommendations.append(f"Fix {len(analysis_report['orphan_pages'])} orphan pages by adding incoming links")
        
        if analysis_report["isolated_clusters"]:
            recommendations.append(f"Connect {len(analysis_report['isolated_clusters'])} isolated clusters to main graph")
        
        if analysis_report["weak_clusters"]:
            recommendations.append(f"Strengthen {len(analysis_report['weak_clusters'])} weak clusters with more internal links")
        
        # Authority distribution recommendations
        authority_variance = analysis_report["authority_distribution"]["authority_variance"]
        if authority_variance > self.graph_thresholds["authority_distribution_variance"]:
            recommendations.append("Balance authority distribution by linking high and low authority pages")
        
        # Graph density recommendations
        graph_density = analysis_report["graph_metrics"]["density"]
        if graph_density < self.graph_thresholds["min_graph_density"]:
            recommendations.append("Increase graph density by adding more internal links")
        
        # Hub page recommendations
        hub_count = len(analysis_report["hub_pages"])
        if hub_count < 10:
            recommendations.append("Create more hub pages to improve connectivity")
        
        # Connectivity recommendations
        connectivity_ratio = analysis_report["connectivity_analysis"]["connectivity_ratio"]
        if connectivity_ratio < 0.95:
            recommendations.append("Improve connectivity to ensure all pages are reachable")
        
        return recommendations
    
    def get_link_graph_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive link graph dashboard"""
        
        dashboard = {
            "summary": {},
            "graph_health": {},
            "connectivity_metrics": {},
            "authority_analysis": {},
            "cluster_analysis": {},
            "recommendations": []
        }
        
        # Get latest analysis data
        analysis_data = cache.get("internal_link_graph_analysis")
        if not analysis_data:
            analysis_data = self.analyze_internal_link_graph()
        
        # Summary metrics
        dashboard["summary"] = {
            "optimization_score": analysis_data["optimization_score"],
            "total_nodes": analysis_data["graph_metrics"]["total_nodes"],
            "total_edges": analysis_data["graph_metrics"]["total_edges"],
            "graph_density": analysis_data["graph_metrics"]["density"],
            "orphan_pages": len(analysis_data["orphan_pages"]),
            "isolated_clusters": len(analysis_data["isolated_clusters"]),
            "hub_pages": len(analysis_data["hub_pages"])
        }
        
        # Graph health
        dashboard["graph_health"] = {
            "health_score": analysis_data["optimization_score"],
            "status": "healthy" if analysis_data["optimization_score"] >= 85 else "needs_improvement",
            "critical_issues": len(analysis_data["orphan_pages"]) + len(analysis_data["isolated_clusters"]),
            "last_analysis": analysis_data["analysis_timestamp"]
        }
        
        # Connectivity metrics
        dashboard["connectivity_metrics"] = {
            "is_connected": analysis_data["connectivity_analysis"]["is_weakly_connected"],
            "connectivity_ratio": analysis_data["connectivity_analysis"]["connectivity_ratio"],
            "largest_component_size": analysis_data["connectivity_analysis"]["largest_component_size"],
            "bridge_edges": len(analysis_data["connectivity_analysis"]["bridge_edges"]),
            "articulation_points": len(analysis_data["connectivity_analysis"]["articulation_points"])
        }
        
        # Authority analysis
        dashboard["authority_analysis"] = {
            "average_authority": analysis_data["authority_distribution"]["average_authority"],
            "authority_variance": analysis_data["authority_distribution"]["authority_variance"],
            "low_authority_count": len(analysis_data["authority_distribution"]["low_authority_pages"]),
            "high_authority_count": len(analysis_data["authority_distribution"]["high_authority_pages"])
        }
        
        # Cluster analysis
        dashboard["cluster_analysis"] = {
            "isolated_clusters": len(analysis_data["isolated_clusters"]),
            "weak_clusters": len(analysis_data["weak_clusters"]),
            "hub_pages": len(analysis_data["hub_pages"]),
            "strongly_connected_components": analysis_data["graph_metrics"]["strongly_connected_components"]
        }
        
        # Recommendations
        dashboard["recommendations"] = analysis_data["recommendations"]
        
        return dashboard


# Singleton instance
internal_link_graph = InternalLinkGraph()
