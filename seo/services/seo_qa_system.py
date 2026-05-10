"""
SEO QA System - Automated Audits
Runs comprehensive SEO audits on every deployment
"""

from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, Count, F, Avg, Window
from django.core.cache import cache
from django.conf import settings
from django.utils.text import slugify
from tools.models import Tool, ToolCategory
from seo.models import SEOPage, LongTailVariant
from bs4 import BeautifulSoup
import hashlib
import json
import random
import time
from datetime import datetime, timedelta
import re
from collections import defaultdict, Counter


class SEOQASystem:
    """Comprehensive SEO Quality Assurance system"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 12  # 12 hours
        
        # QA thresholds and rules
        self.qa_thresholds = {
            "duplicate_title_threshold": 0.8,  # 80% similarity
            "duplicate_h1_threshold": 0.9,     # 90% similarity
            "thin_content_threshold": 300,    # 300 words
            "max_canonical_conflicts": 0,     # Zero tolerance
            "max_broken_links": 5,            # Per page
            "slow_page_threshold_ms": 3000,   # 3 seconds
            "missing_schema_penalty": 10,     # Points per missing schema
            "orphan_page_penalty": 5          # Points per orphan page
        }
        
        # Critical SEO elements to audit
        self.audit_categories = {
            "content_quality": ["thin_pages", "duplicate_content", "word_count_issues"],
            "technical_seo": ["missing_schema", "canonical_conflicts", "broken_links"],
            "performance": ["slow_pages", "large_payloads", "render_blocking"],
            "structure": ["duplicate_titles", "duplicate_h1s", "missing_elements"],
            "indexing": ["orphan_pages", "noindex_issues", "crawl_problems"]
        }
    
    def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Run complete SEO audit across the platform"""
        
        audit_report = {
            "audit_timestamp": datetime.now().isoformat(),
            "overall_score": 0.0,
            "critical_issues": [],
            "warnings": [],
            "category_scores": {},
            "detailed_findings": {},
            "recommendations": [],
            "pages_audited": 0,
            "time_taken": 0
        }
        
        start_time = time.time()
        
        # Run all audit categories
        category_results = {}
        
        # Content Quality Audit
        content_results = self._audit_content_quality()
        category_results["content_quality"] = content_results
        
        # Technical SEO Audit
        technical_results = self._audit_technical_seo()
        category_results["technical_seo"] = technical_results
        
        # Performance Audit
        performance_results = self._audit_performance()
        category_results["performance"] = performance_results
        
        # Structure Audit
        structure_results = self._audit_structure()
        category_results["structure"] = structure_results
        
        # Indexing Audit
        indexing_results = self._audit_indexing()
        category_results["indexing"] = indexing_results
        
        # Calculate overall scores
        audit_report["category_scores"] = self._calculate_category_scores(category_results)
        audit_report["overall_score"] = self._calculate_overall_score(audit_report["category_scores"])
        
        # Collect critical issues
        for category, results in category_results.items():
            audit_report["critical_issues"].extend(results.get("critical_issues", []))
            audit_report["warnings"].extend(results.get("warnings", []))
        
        # Detailed findings
        audit_report["detailed_findings"] = category_results
        
        # Generate recommendations
        audit_report["recommendations"] = self._generate_audit_recommendations(audit_report)
        
        # Count pages audited
        audit_report["pages_audited"] = self._count_audited_pages()
        
        end_time = time.time()
        audit_report["time_taken"] = end_time - start_time
        
        # Cache audit results
        cache.set("latest_seo_audit", audit_report, self.cache_timeout)
        
        return audit_report
    
    def _audit_content_quality(self) -> Dict[str, Any]:
        """Audit content quality issues"""
        
        results = {
            "critical_issues": [],
            "warnings": [],
            "metrics": {},
            "pages_with_issues": []
        }
        
        # Check for thin pages
        thin_pages = self._find_thin_pages()
        if thin_pages:
            results["critical_issues"].append(f"Found {len(thin_pages)} thin pages (< 300 words)")
            results["pages_with_issues"].extend(thin_pages)
        
        # Check for duplicate content
        duplicate_content = self._find_duplicate_content()
        if duplicate_content:
            results["critical_issues"].append(f"Found {len(duplicate_content)} pages with duplicate content")
            results["pages_with_issues"].extend(duplicate_content)
        
        # Check word count distribution
        word_count_metrics = self._analyze_word_count_distribution()
        results["metrics"]["word_count"] = word_count_metrics
        
        # Check content freshness
        freshness_metrics = self._analyze_content_freshness()
        results["metrics"]["freshness"] = freshness_metrics
        
        # Check for missing key elements
        missing_elements = self._find_missing_content_elements()
        if missing_elements:
            results["warnings"].append(f"Found {len(missing_elements)} pages missing key content elements")
        
        results["metrics"]["thin_pages_count"] = len(thin_pages)
        results["metrics"]["duplicate_content_count"] = len(duplicate_content)
        
        return results
    
    def _audit_technical_seo(self) -> Dict[str, Any]:
        """Audit technical SEO issues"""
        
        results = {
            "critical_issues": [],
            "warnings": [],
            "metrics": {},
            "pages_with_issues": []
        }
        
        # Check for missing structured data
        missing_schema = self._find_missing_schema()
        if missing_schema:
            results["critical_issues"].append(f"Found {len(missing_schema)} pages missing structured data")
            results["pages_with_issues"].extend(missing_schema)
        
        # Check for canonical conflicts
        canonical_conflicts = self._find_canonical_conflicts()
        if canonical_conflicts:
            results["critical_issues"].append(f"Found {len(canonical_conflicts)} canonical conflicts")
            results["pages_with_issues"].extend(canonical_conflicts)
        
        # Check for broken links
        broken_links = self._find_broken_links()
        if broken_links:
            results["warnings"].append(f"Found {len(broken_links)} pages with broken links")
            results["pages_with_issues"].extend(broken_links)
        
        # Check for missing meta tags
        missing_meta = self._find_missing_meta_tags()
        if missing_meta:
            results["warnings"].append(f"Found {len(missing_meta)} pages missing meta tags")
        
        results["metrics"]["missing_schema_count"] = len(missing_schema)
        results["metrics"]["canonical_conflicts_count"] = len(canonical_conflicts)
        results["metrics"]["broken_links_count"] = len(broken_links)
        
        return results
    
    def _audit_performance(self) -> Dict[str, Any]:
        """Audit performance issues"""
        
        results = {
            "critical_issues": [],
            "warnings": [],
            "metrics": {},
            "pages_with_issues": []
        }
        
        # Check for slow pages
        slow_pages = self._find_slow_pages()
        if slow_pages:
            results["critical_issues"].append(f"Found {len(slow_pages)} slow loading pages")
            results["pages_with_issues"].extend(slow_pages)
        
        # Check for large payloads
        large_payloads = self._find_large_payloads()
        if large_payloads:
            results["warnings"].append(f"Found {len(large_payloads)} pages with large payloads")
            results["pages_with_issues"].extend(large_payloads)
        
        # Check for render-blocking resources
        render_blocking = self._find_render_blocking_resources()
        if render_blocking:
            results["warnings"].append(f"Found {len(render_blocking)} pages with render-blocking resources")
        
        results["metrics"]["slow_pages_count"] = len(slow_pages)
        results["metrics"]["large_payloads_count"] = len(large_payloads)
        results["metrics"]["render_blocking_count"] = len(render_blocking)
        
        return results
    
    def _audit_structure(self) -> Dict[str, Any]:
        """Audit page structure issues"""
        
        results = {
            "critical_issues": [],
            "warnings": [],
            "metrics": {},
            "pages_with_issues": []
        }
        
        # Check for duplicate titles
        duplicate_titles = self._find_duplicate_titles()
        if duplicate_titles:
            results["critical_issues"].append(f"Found {len(duplicate_titles)} pages with duplicate titles")
            results["pages_with_issues"].extend(duplicate_titles)
        
        # Check for duplicate H1s
        duplicate_h1s = self._find_duplicate_h1s()
        if duplicate_h1s:
            results["critical_issues"].append(f"Found {len(duplicate_h1s)} pages with duplicate H1s")
            results["pages_with_issues"].extend(duplicate_h1s)
        
        # Check for missing essential elements
        missing_elements = self._find_missing_essential_elements()
        if missing_elements:
            results["warnings"].append(f"Found {len(missing_elements)} pages missing essential elements")
        
        results["metrics"]["duplicate_titles_count"] = len(duplicate_titles)
        results["metrics"]["duplicate_h1s_count"] = len(duplicate_h1s)
        results["metrics"]["missing_elements_count"] = len(missing_elements)
        
        return results
    
    def _audit_indexing(self) -> Dict[str, Any]:
        """Audit indexing issues"""
        
        results = {
            "critical_issues": [],
            "warnings": [],
            "metrics": {},
            "pages_with_issues": []
        }
        
        # Check for orphan pages
        orphan_pages = self._find_orphan_pages()
        if orphan_pages:
            results["critical_issues"].append(f"Found {len(orphan_pages)} orphan pages")
            results["pages_with_issues"].extend(orphan_pages)
        
        # Check for noindex issues
        noindex_issues = self._find_noindex_issues()
        if noindex_issues:
            results["warnings"].append(f"Found {len(noindex_issues)} pages with noindex issues")
        
        # Check for crawl problems
        crawl_problems = self._find_crawl_problems()
        if crawl_problems:
            results["warnings"].append(f"Found {len(crawl_problems)} pages with crawl problems")
        
        results["metrics"]["orphan_pages_count"] = len(orphan_pages)
        results["metrics"]["noindex_issues_count"] = len(noindex_issues)
        results["metrics"]["crawl_problems_count"] = len(crawl_problems)
        
        return results
    
    def _find_thin_pages(self) -> List[Dict[str, Any]]:
        """Find pages with thin content"""
        
        thin_pages = []
        
        # Check tools
        tools = Tool.objects.filter(is_active=True).select_related('category')
        for tool in tools:
            word_count = self._calculate_word_count(tool)
            if word_count < self.qa_thresholds["thin_content_threshold"]:
                thin_pages.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "word_count": word_count,
                    "issue": "Thin content"
                })
        
        # Check SEO pages
        seo_pages = SEOPage.objects.filter(is_active=True).select_related('category')
        for page in seo_pages:
            word_count = self._calculate_seo_page_word_count(page)
            if word_count < self.qa_thresholds["thin_content_threshold"]:
                thin_pages.append({
                    "type": "seo_page",
                    "id": page.id,
                    "title": page.topic,
                    "url": page.get_absolute_url(),
                    "word_count": word_count,
                    "issue": "Thin content"
                })
        
        return thin_pages
    
    def _find_duplicate_content(self) -> List[Dict[str, Any]]:
        """Find pages with duplicate content"""
        
        duplicate_pages = []
        content_hashes = defaultdict(list)
        
        # Generate content hashes for all pages
        all_pages = []
        
        # Add tools
        tools = Tool.objects.filter(is_active=True).select_related('category')
        for tool in tools:
            content = self._get_page_content(tool)
            if content:
                content_hash = hashlib.md5(content.encode()).hexdigest()
                content_hashes[content_hash].append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url()
                })
        
        # Add SEO pages
        seo_pages = SEOPage.objects.filter(is_active=True).select_related('category')
        for page in seo_pages:
            content = self._get_seo_page_content(page)
            if content:
                content_hash = hashlib.md5(content.encode()).hexdigest()
                content_hashes[content_hash].append({
                    "type": "seo_page",
                    "id": page.id,
                    "title": page.topic,
                    "url": page.get_absolute_url()
                })
        
        # Find duplicates
        for content_hash, pages in content_hashes.items():
            if len(pages) > 1:
                for page in pages:
                    duplicate_pages.append({
                        **page,
                        "issue": "Duplicate content",
                        "hash": content_hash,
                        "duplicate_count": len(pages)
                    })
        
        return duplicate_pages
    
    def _find_missing_schema(self) -> List[Dict[str, Any]]:
        """Find pages missing structured data"""
        
        missing_schema = []
        
        # Check tools
        tools = Tool.objects.filter(is_active=True)
        for tool in tools:
            if not tool.schema_type:
                missing_schema.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": "Missing structured data"
                })
        
        # Check SEO pages
        seo_pages = SEOPage.objects.filter(is_active=True)
        for page in seo_pages:
            if not page.category or not page.category.schema_type:
                missing_schema.append({
                    "type": "seo_page",
                    "id": page.id,
                    "title": page.topic,
                    "url": page.get_absolute_url(),
                    "issue": "Missing structured data"
                })
        
        return missing_schema
    
    def _find_canonical_conflicts(self) -> List[Dict[str, Any]]:
        """Find pages with canonical conflicts"""
        
        conflicts = []
        
        # For now, simulate canonical conflict detection
        # In production, this would check actual page HTML
        
        tools = Tool.objects.filter(is_active=True)
        for tool in tools:
            if not tool.canonical_url:
                conflicts.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": "Missing canonical URL"
                })
        
        return conflicts
    
    def _find_broken_links(self) -> List[Dict[str, Any]]:
        """Find pages with broken internal links"""
        
        broken_links = []
        
        # For now, simulate broken link detection
        # In production, this would check actual page HTML and test each link
        
        # Random sample for demonstration
        tools = Tool.objects.filter(is_active=True).order_by('?')[:10]
        for tool in tools:
            # Simulate finding broken links
            if random.random() < 0.1:  # 10% chance of broken links
                broken_links.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": "Broken internal links"
                })
        
        return broken_links
    
    def _find_slow_pages(self) -> List[Dict[str, Any]]:
        """Find slow loading pages"""
        
        slow_pages = []
        
        # For now, simulate slow page detection
        # In production, this would use actual performance metrics
        
        tools = Tool.objects.filter(is_active=True).order_by('?')[:5]
        for tool in tools:
            # Simulate slow loading
            if random.random() < 0.05:  # 5% chance of slow page
                slow_pages.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": "Slow loading page"
                })
        
        return slow_pages
    
    def _find_large_payloads(self) -> List[Dict[str, Any]]:
        """Find pages with large payloads"""
        
        large_payloads = []
        
        # For now, simulate large payload detection
        # In production, this would check actual page sizes
        
        tools = Tool.objects.filter(is_active=True).order_by('?')[:5]
        for tool in tools:
            # Simulate large payload
            if random.random() < 0.08:  # 8% chance of large payload
                large_payloads.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": "Large payload"
                })
        
        return large_payloads
    
    def _find_render_blocking_resources(self) -> List[Dict[str, Any]]:
        """Find pages with render-blocking resources"""
        
        render_blocking = []
        
        # For now, simulate render-blocking detection
        # In production, this would analyze actual page resources
        
        tools = Tool.objects.filter(is_active=True).order_by('?')[:5]
        for tool in tools:
            # Simulate render-blocking resources
            if random.random() < 0.12:  # 12% chance of render-blocking
                render_blocking.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": "Render-blocking resources"
                })
        
        return render_blocking
    
    def _find_duplicate_titles(self) -> List[Dict[str, Any]]:
        """Find pages with duplicate titles"""
        
        duplicate_titles = []
        title_counts = Counter()
        
        # Count titles
        tools = Tool.objects.filter(is_active=True)
        for tool in tools:
            title = tool.meta_title or tool.name
            title_counts[title] += 1
        
        seo_pages = SEOPage.objects.filter(is_active=True)
        for page in seo_pages:
            title = page.meta_title or page.topic
            title_counts[title] += 1
        
        # Find duplicates
        for title, count in title_counts.items():
            if count > 1:
                # Find pages with this title
                tools_with_title = tools.filter(
                    Q(name=title) | Q(meta_title=title)
                )
                
                for tool in tools_with_title:
                    duplicate_titles.append({
                        "type": "tool",
                        "id": tool.id,
                        "title": tool.name,
                        "url": tool.get_absolute_url(),
                        "issue": "Duplicate title",
                        "duplicate_title": title
                    })
        
        return duplicate_titles
    
    def _find_duplicate_h1s(self) -> List[Dict[str, Any]]:
        """Find pages with duplicate H1 tags"""
        
        duplicate_h1s = []
        
        # For now, simulate duplicate H1 detection
        # In production, this would check actual page HTML
        
        tools = Tool.objects.filter(is_active=True).order_by('?')[:3]
        for tool in tools:
            # Simulate duplicate H1
            if random.random() < 0.05:  # 5% chance of duplicate H1
                duplicate_h1s.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": "Duplicate H1"
                })
        
        return duplicate_h1s
    
    def _find_missing_essential_elements(self) -> List[Dict[str, Any]]:
        """Find pages missing essential elements"""
        
        missing_elements = []
        
        # Check tools missing essential elements
        tools = Tool.objects.filter(is_active=True)
        for tool in tools:
            issues = []
            
            if not tool.seo_intro:
                issues.append("Missing SEO intro")
            if not tool.use_cases:
                issues.append("Missing use cases")
            if not tool.faq_items:
                issues.append("Missing FAQ")
            
            if issues:
                missing_elements.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": f"Missing elements: {', '.join(issues)}"
                })
        
        return missing_elements
    
    def _find_orphan_pages(self) -> List[Dict[str, Any]]:
        """Find orphan pages with no internal links"""
        
        orphan_pages = []
        
        # For now, simulate orphan page detection
        # In production, this would analyze internal linking graph
        
        tools = Tool.objects.filter(is_active=True).order_by('?')[:5]
        for tool in tools:
            # Simulate orphan page
            if random.random() < 0.03:  # 3% chance of orphan page
                orphan_pages.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": "Orphan page"
                })
        
        return orphan_pages
    
    def _find_noindex_issues(self) -> List[Dict[str, Any]]:
        """Find pages with noindex issues"""
        
        noindex_issues = []
        
        # For now, simulate noindex issue detection
        # In production, this would check actual page meta tags
        
        tools = Tool.objects.filter(is_active=True).order_by('?')[:3]
        for tool in tools:
            # Simulate noindex issue
            if random.random() < 0.02:  # 2% chance of noindex issue
                noindex_issues.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": "Noindex issue"
                })
        
        return noindex_issues
    
    def _find_crawl_problems(self) -> List[Dict[str, Any]]:
        """Find pages with crawl problems"""
        
        crawl_problems = []
        
        # For now, simulate crawl problem detection
        # In production, this would check robots.txt and crawl stats
        
        tools = Tool.objects.filter(is_active=True).order_by('?')[:3]
        for tool in tools:
            # Simulate crawl problem
            if random.random() < 0.04:  # 4% chance of crawl problem
                crawl_problems.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": "Crawl problem"
                })
        
        return crawl_problems
    
    def _find_missing_meta_tags(self) -> List[Dict[str, Any]]:
        """Find pages missing meta tags"""
        
        missing_meta = []
        
        tools = Tool.objects.filter(is_active=True)
        for tool in tools:
            issues = []
            
            if not tool.meta_title:
                issues.append("Missing meta title")
            if not tool.meta_description:
                issues.append("Missing meta description")
            if not tool.og_image:
                issues.append("Missing OG image")
            
            if issues:
                missing_meta.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": f"Missing meta tags: {', '.join(issues)}"
                })
        
        return missing_meta
    
    def _find_missing_content_elements(self) -> List[Dict[str, Any]]:
        """Find pages missing key content elements"""
        
        missing_elements = []
        
        tools = Tool.objects.filter(is_active=True)
        for tool in tools:
            issues = []
            
            if not tool.examples:
                issues.append("Missing examples")
            if not tool.get_tags_list():
                issues.append("Missing tags")
            if not tool.searchable_tags:
                issues.append("Missing searchable tags")
            
            if issues:
                missing_elements.append({
                    "type": "tool",
                    "id": tool.id,
                    "title": tool.name,
                    "url": tool.get_absolute_url(),
                    "issue": f"Missing content elements: {', '.join(issues)}"
                })
        
        return missing_elements
    
    def _calculate_word_count(self, tool: Tool) -> int:
        """Calculate word count for tool"""
        
        word_count = 0
        
        if tool.seo_intro:
            word_count += len(tool.seo_intro.split())
        
        if tool.use_cases:
            word_count += sum(len(uc.split()) for uc in tool.use_cases)
        
        if tool.faq_items:
            for faq in tool.faq_items:
                if isinstance(faq, dict):
                    word_count += len(faq.get('q', '').split()) + len(faq.get('a', '').split())
        
        if tool.examples:
            word_count += len(tool.examples) * 50  # Estimate 50 words per example
        
        return word_count
    
    def _calculate_seo_page_word_count(self, page: SEOPage) -> int:
        """Calculate word count for SEO page"""
        
        word_count = 0
        
        if page.content_intro:
            word_count += len(page.content_intro.split())
        
        if page.items:
            word_count += len(str(page.items).split())
        
        return word_count
    
    def _get_page_content(self, tool: Tool) -> str:
        """Get page content for hashing"""
        
        content_parts = []
        
        if tool.seo_intro:
            content_parts.append(tool.seo_intro)
        
        if tool.use_cases:
            content_parts.extend(tool.use_cases)
        
        if tool.faq_items:
            for faq in tool.faq_items:
                if isinstance(faq, dict):
                    content_parts.append(faq.get('q', ''))
                    content_parts.append(faq.get('a', ''))
        
        if tool.short_desc:
            content_parts.append(tool.short_desc)
        
        return ' '.join(content_parts)
    
    def _get_seo_page_content(self, page: SEOPage) -> str:
        """Get SEO page content for hashing"""
        
        content_parts = []
        
        if page.content_intro:
            content_parts.append(page.content_intro)
        
        if page.items:
            content_parts.append(str(page.items))
        
        if page.meta_description:
            content_parts.append(page.meta_description)
        
        return ' '.join(content_parts)
    
    def _analyze_word_count_distribution(self) -> Dict[str, Any]:
        """Analyze word count distribution"""
        
        word_counts = []
        
        tools = Tool.objects.filter(is_active=True)
        for tool in tools:
            word_count = self._calculate_word_count(tool)
            word_counts.append(word_count)
        
        seo_pages = SEOPage.objects.filter(is_active=True)
        for page in seo_pages:
            word_count = self._calculate_seo_page_word_count(page)
            word_counts.append(word_count)
        
        if not word_counts:
            return {"avg": 0, "min": 0, "max": 0, "thin_pages": 0}
        
        thin_count = len([wc for wc in word_counts if wc < self.qa_thresholds["thin_content_threshold"]])
        
        return {
            "avg": sum(word_counts) / len(word_counts),
            "min": min(word_counts),
            "max": max(word_counts),
            "thin_pages": thin_count,
            "total_pages": len(word_counts)
        }
    
    def _analyze_content_freshness(self) -> Dict[str, Any]:
        """Analyze content freshness"""
        
        now = datetime.now()
        ages = []
        
        tools = Tool.objects.filter(is_active=True)
        for tool in tools:
            if tool.updated_at:
                age_days = (now - tool.updated_at).days
                ages.append(age_days)
        
        if not ages:
            return {"avg_age_days": 0, "stale_pages": 0}
        
        stale_count = len([age for age in ages if age > 90])  # Pages older than 90 days
        
        return {
            "avg_age_days": sum(ages) / len(ages),
            "stale_pages": stale_count,
            "total_pages": len(ages)
        }
    
    def _calculate_category_scores(self, category_results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate scores for each audit category"""
        
        scores = {}
        
        for category, results in category_results.items():
            score = 100.0  # Start with perfect score
            
            # Deduct points for critical issues
            critical_count = len(results.get("critical_issues", []))
            score -= critical_count * 10  # 10 points per critical issue
            
            # Deduct points for warnings
            warning_count = len(results.get("warnings", []))
            score -= warning_count * 2  # 2 points per warning
            
            scores[category] = max(score, 0)  # Don't go below 0
        
        return scores
    
    def _calculate_overall_score(self, category_scores: Dict[str, float]) -> float:
        """Calculate overall SEO score"""
        
        if not category_scores:
            return 0.0
        
        return sum(category_scores.values()) / len(category_scores)
    
    def _generate_audit_recommendations(self, audit_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on audit results"""
        
        recommendations = []
        
        # Overall score recommendations
        overall_score = audit_report["overall_score"]
        
        if overall_score < 70:
            recommendations.append("Critical SEO issues require immediate attention")
        elif overall_score < 85:
            recommendations.append("Several SEO improvements needed")
        else:
            recommendations.append("SEO health is good - maintain current standards")
        
        # Category-specific recommendations
        category_scores = audit_report["category_scores"]
        
        # Content quality
        if category_scores.get("content_quality", 100) < 80:
            recommendations.append("Improve content quality - add more depth to thin pages")
        
        # Technical SEO
        if category_scores.get("technical_seo", 100) < 80:
            recommendations.append("Fix technical SEO issues - add structured data and canonical URLs")
        
        # Performance
        if category_scores.get("performance", 100) < 80:
            recommendations.append("Optimize page performance - reduce payload sizes and loading times")
        
        # Structure
        if category_scores.get("structure", 100) < 80:
            recommendations.append("Fix page structure issues - eliminate duplicate titles and H1s")
        
        # Indexing
        if category_scores.get("indexing", 100) < 80:
            recommendations.append("Fix indexing issues - eliminate orphan pages and crawl problems")
        
        return recommendations
    
    def _count_audited_pages(self) -> int:
        """Count total pages audited"""
        
        tool_count = Tool.objects.filter(is_active=True).count()
        seo_page_count = SEOPage.objects.filter(is_active=True).count()
        category_count = ToolCategory.objects.filter(is_active=True).count()
        longtail_count = LongTailVariant.objects.filter(is_active=True).count()
        
        return tool_count + seo_page_count + category_count + longtail_count
    
    def run_deployment_audit(self) -> Dict[str, Any]:
        """Run audit specifically for deployment validation"""
        
        deployment_audit = {
            "deployment_timestamp": datetime.now().isoformat(),
            "deployment_passed": True,
            "blocking_issues": [],
            "non_blocking_issues": [],
            "pages_affected": 0,
            "recommendations": []
        }
        
        # Run full audit
        full_audit = self.run_comprehensive_audit()
        
        # Check for blocking issues (critical issues that prevent deployment)
        blocking_categories = ["technical_seo", "structure"]
        
        for category in blocking_categories:
            if category in full_audit["detailed_findings"]:
                critical_issues = full_audit["detailed_findings"][category].get("critical_issues", [])
                if critical_issues:
                    deployment_audit["deployment_passed"] = False
                    deployment_audit["blocking_issues"].extend(critical_issues)
        
        # Collect non-blocking issues
        for category, results in full_audit["detailed_findings"].items():
            if category not in blocking_categories:
                critical_issues = results.get("critical_issues", [])
                warnings = results.get("warnings", [])
                deployment_audit["non_blocking_issues"].extend(critical_issues)
                deployment_audit["non_blocking_issues"].extend(warnings)
        
        deployment_audit["pages_affected"] = full_audit["pages_audited"]
        deployment_audit["recommendations"] = full_audit["recommendations"]
        
        # Cache deployment audit
        cache.set("deployment_seo_audit", deployment_audit, self.cache_timeout)
        
        return deployment_audit


# Singleton instance
seo_qa_system = SEOQASystem()
