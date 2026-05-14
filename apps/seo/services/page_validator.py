"""
Indexable Page Creation Validation System
Validates pages exist physically, resolve correctly, and meet SEO requirements
"""

from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, Count, F, Avg
from django.core.cache import cache
from django.conf import settings
from django.test import Client
from django.urls import reverse
from django.utils.text import slugify
from apps.tools.models import Tool, ToolCategory
from apps.seo.models import SEOPage, LongTailVariant
from bs4 import BeautifulSoup
import requests
import json
import time
from datetime import datetime, timedelta
import re


class PageValidator:
    """Comprehensive page validation system"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 2  # 2 hours
        self.client = Client()
        self.validation_thresholds = {
            "response_time_ms": 2000,
            "min_content_length": 500,
            "min_word_count": 100,
            "max_redirects": 2
        }
        
        # Critical SEO elements to validate
        self.critical_elements = {
            "title": {"required": True, "min_length": 30, "max_length": 70},
            "meta_description": {"required": True, "min_length": 120, "max_length": 160},
            "h1": {"required": True, "min_length": 10, "max_length": 100},
            "canonical": {"required": True, "valid_url": True},
            "structured_data": {"required": True, "valid_json": True},
            "robots_meta": {"required": True, "allow_index": True},
            "viewport": {"required": True, "content": "width=device-width"}
        }
    
    def validate_indexable_pages(self, sample_size: int = 1000) -> Dict[str, Any]:
        """Validate indexable page creation across the platform"""
        
        validation_report = {
            "total_pages_tested": 0,
            "validation_summary": {},
            "failed_pages": [],
            "performance_metrics": {},
            "seo_compliance": {},
            "sitemap_validation": {},
            "robots_txt_validation": {},
            "recommendations": [],
            "time_taken": 0
        }
        
        start_time = time.time()
        
        # Get pages to validate
        pages_to_test = self._get_pages_for_validation(sample_size)
        validation_report["total_pages_tested"] = len(pages_to_test)
        
        # Validate each page
        validation_results = []
        for page_data in pages_to_test:
            result = self._validate_single_page(page_data)
            validation_results.append(result)
            
            if not result["passed"]:
                validation_report["failed_pages"].append(result)
        
        # Calculate summary metrics
        validation_report["validation_summary"] = self._calculate_validation_summary(validation_results)
        validation_report["performance_metrics"] = self._calculate_performance_metrics(validation_results)
        validation_report["seo_compliance"] = self._calculate_seo_compliance(validation_results)
        
        # Validate sitemap and robots.txt
        validation_report["sitemap_validation"] = self._validate_sitemap()
        validation_report["robots_txt_validation"] = self._validate_robots_txt()
        
        # Generate recommendations
        validation_report["recommendations"] = self._generate_validation_recommendations(validation_report)
        
        end_time = time.time()
        validation_report["time_taken"] = end_time - start_time
        
        return validation_report
    
    def _get_pages_for_validation(self, sample_size: int) -> List[Dict[str, Any]]:
        """Get representative sample of pages for validation"""
        
        pages = []
        
        # Sample tools (40% of sample)
        tool_count = int(sample_size * 0.4)
        tools = Tool.objects.filter(is_active=True).select_related('category')[:tool_count]
        
        for tool in tools:
            pages.append({
                "type": "tool",
                "url": tool.get_absolute_url(),
                "id": tool.id,
                "title": tool.name,
                "category": tool.category.name if tool.category else None
            })
        
        # Sample SEO pages (30% of sample)
        seo_count = int(sample_size * 0.3)
        seo_pages = SEOPage.objects.filter(is_active=True).select_related('category')[:seo_count]
        
        for page in seo_pages:
            pages.append({
                "type": "seo_page",
                "url": page.get_absolute_url(),
                "id": page.id,
                "title": page.topic,
                "category": page.category.name if page.category else None
            })
        
        # Sample categories (20% of sample)
        category_count = int(sample_size * 0.2)
        categories = ToolCategory.objects.filter(is_active=True)[:category_count]
        
        for category in categories:
            pages.append({
                "type": "category",
                "url": category.get_absolute_url(),
                "id": category.id,
                "title": category.name,
                "category": category.name
            })
        
        # Sample longtail variants (10% of sample)
        longtail_count = int(sample_size * 0.1)
        longtails = LongTailVariant.objects.filter(is_active=True).select_related('tool')[:longtail_count]
        
        for variant in longtails:
            pages.append({
                "type": "longtail",
                "url": variant.get_absolute_url(),
                "id": variant.id,
                "title": variant.title,
                "category": variant.tool.category.name if variant.tool.category else None
            })
        
        return pages[:sample_size]
    
    def _validate_single_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single page comprehensively"""
        
        result = {
            "page_type": page_data["type"],
            "url": page_data["url"],
            "title": page_data["title"],
            "passed": True,
            "errors": [],
            "warnings": [],
            "performance": {},
            "seo_elements": {},
            "content_metrics": {},
            "validation_timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test HTTP response
            response = self._test_http_response(page_data["url"])
            result["performance"]["response_time_ms"] = response["response_time_ms"]
            result["performance"]["status_code"] = response["status_code"]
            result["performance"]["content_length"] = response["content_length"]
            
            if response["status_code"] != 200:
                result["passed"] = False
                result["errors"].append(f"HTTP {response['status_code']}: {response['error']}")
                return result
            
            # Parse HTML content
            soup = BeautifulSoup(response["content"], 'html.parser')
            
            # Validate critical SEO elements
            seo_validation = self._validate_seo_elements(soup, page_data)
            result["seo_elements"] = seo_validation
            
            if not seo_validation["passed"]:
                result["passed"] = False
                result["errors"].extend(seo_validation["errors"])
            
            # Validate content metrics
            content_metrics = self._validate_content_metrics(soup, page_data)
            result["content_metrics"] = content_metrics
            
            if not content_metrics["passed"]:
                result["passed"] = False
                result["errors"].extend(content_metrics["errors"])
            
            # Validate structured data
            structured_data_validation = self._validate_structured_data(soup)
            if not structured_data_validation["passed"]:
                result["passed"] = False
                result["errors"].extend(structured_data_validation["errors"])
            
            # Check for performance issues
            if response["response_time_ms"] > self.validation_thresholds["response_time_ms"]:
                result["warnings"].append(f"Slow response time: {response['response_time_ms']}ms")
            
            # Check content length
            if response["content_length"] < self.validation_thresholds["min_content_length"]:
                result["warnings"].append(f"Low content length: {response['content_length']} bytes")
            
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"Validation failed: {str(e)}")
        
        return result
    
    def _test_http_response(self, url: str) -> Dict[str, Any]:
        """Test HTTP response for a URL"""
        
        result = {
            "status_code": 0,
            "response_time_ms": 0,
            "content_length": 0,
            "content": "",
            "error": None
        }
        
        try:
            start_time = time.time()
            
            # Try Django test client first
            try:
                response = self.client.get(url, follow=True)
                result["status_code"] = response.status_code
                result["content"] = response.content.decode('utf-8', errors='ignore')
                result["content_length"] = len(result["content"])
            except:
                # Fall back to requests for external URLs
                response = requests.get(f"http://localhost:8000{url}", timeout=10)
                result["status_code"] = response.status_code
                result["content"] = response.text
                result["content_length"] = len(result["content"])
            
            result["response_time_ms"] = int((time.time() - start_time) * 1000)
            
        except requests.exceptions.Timeout:
            result["error"] = "Request timeout"
        except requests.exceptions.ConnectionError:
            result["error"] = "Connection error"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _validate_seo_elements(self, soup: BeautifulSoup, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate critical SEO elements"""
        
        validation = {
            "passed": True,
            "errors": [],
            "elements_found": {}
        }
        
        # Check title tag
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text().strip()
            validation["elements_found"]["title"] = {
                "found": True,
                "content": title_text,
                "length": len(title_text)
            }
            
            if len(title_text) < self.critical_elements["title"]["min_length"]:
                validation["errors"].append(f"Title too short: {len(title_text)} chars")
                validation["passed"] = False
            elif len(title_text) > self.critical_elements["title"]["max_length"]:
                validation["errors"].append(f"Title too long: {len(title_text)} chars")
                validation["passed"] = False
        else:
            validation["errors"].append("Missing title tag")
            validation["passed"] = False
            validation["elements_found"]["title"] = {"found": False}
        
        # Check meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            desc_content = meta_desc.get('content', '').strip()
            validation["elements_found"]["meta_description"] = {
                "found": True,
                "content": desc_content,
                "length": len(desc_content)
            }
            
            if len(desc_content) < self.critical_elements["meta_description"]["min_length"]:
                validation["errors"].append(f"Meta description too short: {len(desc_content)} chars")
                validation["passed"] = False
            elif len(desc_content) > self.critical_elements["meta_description"]["max_length"]:
                validation["errors"].append(f"Meta description too long: {len(desc_content)} chars")
                validation["passed"] = False
        else:
            validation["errors"].append("Missing meta description")
            validation["passed"] = False
            validation["elements_found"]["meta_description"] = {"found": False}
        
        # Check H1 tag
        h1_tag = soup.find('h1')
        if h1_tag:
            h1_text = h1_tag.get_text().strip()
            validation["elements_found"]["h1"] = {
                "found": True,
                "content": h1_text,
                "length": len(h1_text)
            }
            
            if len(h1_text) < self.critical_elements["h1"]["min_length"]:
                validation["errors"].append(f"H1 too short: {len(h1_text)} chars")
                validation["passed"] = False
        else:
            validation["errors"].append("Missing H1 tag")
            validation["passed"] = False
            validation["elements_found"]["h1"] = {"found": False}
        
        # Check canonical link
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical:
            canonical_url = canonical.get('href', '')
            validation["elements_found"]["canonical"] = {
                "found": True,
                "url": canonical_url
            }
            
            if not canonical_url:
                validation["errors"].append("Canonical URL is empty")
                validation["passed"] = False
        else:
            validation["errors"].append("Missing canonical link")
            validation["passed"] = False
            validation["elements_found"]["canonical"] = {"found": False}
        
        # Check robots meta
        robots_meta = soup.find('meta', attrs={'name': 'robots'})
        if robots_meta:
            robots_content = robots_meta.get('content', '').lower()
            validation["elements_found"]["robots_meta"] = {
                "found": True,
                "content": robots_content
            }
            
            if 'noindex' in robots_content:
                validation["errors"].append("Page has noindex directive")
                validation["passed"] = False
        else:
            validation["elements_found"]["robots_meta"] = {"found": False}
        
        # Check viewport meta
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if viewport:
            viewport_content = viewport.get('content', '')
            validation["elements_found"]["viewport"] = {
                "found": True,
                "content": viewport_content
            }
        else:
            validation["elements_found"]["viewport"] = {"found": False}
        
        return validation
    
    def _validate_content_metrics(self, soup: BeautifulSoup, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content quality metrics"""
        
        validation = {
            "passed": True,
            "errors": [],
            "metrics": {}
        }
        
        # Get text content
        text_content = soup.get_text()
        word_count = len(text_content.split())
        
        validation["metrics"]["word_count"] = word_count
        validation["metrics"]["character_count"] = len(text_content)
        
        # Check word count threshold
        if word_count < self.validation_thresholds["min_word_count"]:
            validation["errors"].append(f"Content too short: {word_count} words")
            validation["passed"] = False
        
        # Check for duplicate H1s
        h1_tags = soup.find_all('h1')
        if len(h1_tags) > 1:
            validation["errors"].append(f"Multiple H1 tags found: {len(h1_tags)}")
            validation["passed"] = False
        
        validation["metrics"]["h1_count"] = len(h1_tags)
        
        # Check heading structure
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        validation["metrics"]["total_headings"] = len(headings)
        
        # Check for images with alt text
        images = soup.find_all('img')
        images_with_alt = [img for img in images if img.get('alt')]
        validation["metrics"]["total_images"] = len(images)
        validation["metrics"]["images_with_alt"] = len(images_with_alt)
        
        # Check for internal links
        internal_links = soup.find_all('a', href=True)
        internal_links = [link for link in internal_links if link['href'].startswith('/')]
        validation["metrics"]["internal_links_count"] = len(internal_links)
        
        return validation
    
    def _validate_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Validate structured data (JSON-LD)"""
        
        validation = {
            "passed": True,
            "errors": [],
            "schemas_found": []
        }
        
        # Find JSON-LD scripts
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in json_ld_scripts:
            try:
                schema_data = json.loads(script.string)
                validation["schemas_found"].append({
                    "type": schema_data.get("@type", "Unknown"),
                    "valid": True
                })
            except json.JSONDecodeError as e:
                validation["errors"].append(f"Invalid JSON-LD: {str(e)}")
                validation["passed"] = False
                validation["schemas_found"].append({
                    "type": "Invalid",
                    "valid": False,
                    "error": str(e)
                })
        
        if not json_ld_scripts:
            validation["errors"].append("No structured data found")
            validation["passed"] = False
        
        return validation
    
    def _calculate_validation_summary(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall validation summary"""
        
        summary = {
            "total_pages": len(validation_results),
            "passed_pages": 0,
            "failed_pages": 0,
            "pass_rate": 0.0,
            "error_distribution": {},
            "performance_summary": {},
            "page_type_breakdown": {}
        }
        
        # Count passed/failed
        for result in validation_results:
            if result["passed"]:
                summary["passed_pages"] += 1
            else:
                summary["failed_pages"] += 1
        
        if summary["total_pages"] > 0:
            summary["pass_rate"] = (summary["passed_pages"] / summary["total_pages"]) * 100
        
        # Error distribution
        error_counts = {}
        for result in validation_results:
            for error in result["errors"]:
                error_type = error.split(':')[0]  # Get error type
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        summary["error_distribution"] = error_counts
        
        # Performance summary
        response_times = [r["performance"].get("response_time_ms", 0) for r in validation_results if "performance" in r]
        if response_times:
            summary["performance_summary"] = {
                "avg_response_time_ms": sum(response_times) / len(response_times),
                "max_response_time_ms": max(response_times),
                "min_response_time_ms": min(response_times)
            }
        
        # Page type breakdown
        type_counts = {}
        for result in validation_results:
            page_type = result["page_type"]
            if page_type not in type_counts:
                type_counts[page_type] = {"total": 0, "passed": 0}
            type_counts[page_type]["total"] += 1
            if result["passed"]:
                type_counts[page_type]["passed"] += 1
        
        summary["page_type_breakdown"] = type_counts
        
        return summary
    
    def _calculate_performance_metrics(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        
        metrics = {
            "response_time_distribution": {
                "fast": 0,    # < 500ms
                "medium": 0,  # 500-1000ms
                "slow": 0,    # 1000-2000ms
                "very_slow": 0 # > 2000ms
            },
            "content_length_stats": {},
            "status_code_distribution": {}
        }
        
        response_times = []
        content_lengths = []
        status_codes = []
        
        for result in validation_results:
            if "performance" in result:
                perf = result["performance"]
                
                # Response time distribution
                rt = perf.get("response_time_ms", 0)
                response_times.append(rt)
                
                if rt < 500:
                    metrics["response_time_distribution"]["fast"] += 1
                elif rt < 1000:
                    metrics["response_time_distribution"]["medium"] += 1
                elif rt < 2000:
                    metrics["response_time_distribution"]["slow"] += 1
                else:
                    metrics["response_time_distribution"]["very_slow"] += 1
                
                # Status code distribution
                sc = perf.get("status_code", 0)
                status_codes.append(sc)
                if sc not in metrics["status_code_distribution"]:
                    metrics["status_code_distribution"][sc] = 0
                metrics["status_code_distribution"][sc] += 1
                
                # Content length
                cl = perf.get("content_length", 0)
                content_lengths.append(cl)
        
        # Content length statistics
        if content_lengths:
            metrics["content_length_stats"] = {
                "avg": sum(content_lengths) / len(content_lengths),
                "min": min(content_lengths),
                "max": max(content_lengths)
            }
        
        return metrics
    
    def _calculate_seo_compliance(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate SEO compliance metrics"""
        
        compliance = {
            "title_compliance": {"found": 0, "valid_length": 0, "total": len(validation_results)},
            "meta_desc_compliance": {"found": 0, "valid_length": 0, "total": len(validation_results)},
            "h1_compliance": {"found": 0, "valid_length": 0, "total": len(validation_results)},
            "canonical_compliance": {"found": 0, "total": len(validation_results)},
            "structured_data_compliance": {"found": 0, "valid": 0, "total": len(validation_results)}
        }
        
        for result in validation_results:
            if "seo_elements" in result:
                seo = result["seo_elements"]
                
                # Title compliance
                if seo.get("elements_found", {}).get("title", {}).get("found"):
                    compliance["title_compliance"]["found"] += 1
                    title_length = seo["elements_found"]["title"]["length"]
                    if 30 <= title_length <= 70:
                        compliance["title_compliance"]["valid_length"] += 1
                
                # Meta description compliance
                if seo.get("elements_found", {}).get("meta_description", {}).get("found"):
                    compliance["meta_desc_compliance"]["found"] += 1
                    desc_length = seo["elements_found"]["meta_description"]["length"]
                    if 120 <= desc_length <= 160:
                        compliance["meta_desc_compliance"]["valid_length"] += 1
                
                # H1 compliance
                if seo.get("elements_found", {}).get("h1", {}).get("found"):
                    compliance["h1_compliance"]["found"] += 1
                    h1_length = seo["elements_found"]["h1"]["length"]
                    if h1_length >= 10:
                        compliance["h1_compliance"]["valid_length"] += 1
                
                # Canonical compliance
                if seo.get("elements_found", {}).get("canonical", {}).get("found"):
                    compliance["canonical_compliance"]["found"] += 1
        
        # Calculate compliance percentages
        for metric in compliance:
            if compliance[metric]["total"] > 0:
                if "found" in compliance[metric]:
                    compliance[metric]["found_percentage"] = (
                        compliance[metric]["found"] / compliance[metric]["total"] * 100
                    )
                if "valid_length" in compliance[metric]:
                    compliance[metric]["valid_length_percentage"] = (
                        compliance[metric]["valid_length"] / compliance[metric]["total"] * 100
                    )
        
        return compliance
    
    def _validate_sitemap(self) -> Dict[str, Any]:
        """Validate sitemap accessibility and content"""
        
        validation = {
            "sitemap_accessible": False,
            "sitemap_urls_count": 0,
            "last_modification": None,
            "errors": [],
            "url_validation": {}
        }
        
        try:
            # Test main sitemap
            sitemap_url = "/sitemap.xml"
            response = self._test_http_response(sitemap_url)
            
            if response["status_code"] == 200:
                validation["sitemap_accessible"] = True
                
                # Parse sitemap XML
                soup = BeautifulSoup(response["content"], 'xml')
                urls = soup.find_all('url')
                validation["sitemap_urls_count"] = len(urls)
                
                # Check last modification
                if urls:
                    last_mods = [url.find('lastmod') for url in urls if url.find('lastmod')]
                    if last_mods:
                        validation["last_modification"] = last_mods[0].get_text()
                
                # Validate sample URLs from sitemap
                sample_urls = urls[:10]  # Check first 10 URLs
                valid_urls = 0
                
                for url_element in sample_urls:
                    loc = url_element.find('loc')
                    if loc:
                        url_path = loc.get_text().replace('http://localhost:8000', '')
                        url_response = self._test_http_response(url_path)
                        if url_response["status_code"] == 200:
                            valid_urls += 1
                
                validation["url_validation"] = {
                    "sample_checked": len(sample_urls),
                    "valid_urls": valid_urls,
                    "validity_rate": (valid_urls / len(sample_urls) * 100) if sample_urls else 0
                }
            else:
                validation["errors"].append(f"Sitemap not accessible: HTTP {response['status_code']}")
        
        except Exception as e:
            validation["errors"].append(f"Sitemap validation failed: {str(e)}")
        
        return validation
    
    def _validate_robots_txt(self) -> Dict[str, Any]:
        """Validate robots.txt file"""
        
        validation = {
            "robots_accessible": False,
            "allows_crawling": False,
            "sitemaps_referenced": 0,
            "errors": [],
            "directives": {}
        }
        
        try:
            # Test robots.txt
            robots_url = "/robots.txt"
            response = self._test_http_response(robots_url)
            
            if response["status_code"] == 200:
                validation["robots_accessible"] = True
                
                content = response["content"]
                lines = content.split('\n')
                
                disallow_count = 0
                allow_count = 0
                sitemap_count = 0
                
                for line in lines:
                    line = line.strip().lower()
                    
                    if line.startswith('disallow:'):
                        if line == 'disallow: /':
                            validation["allows_crawling"] = False
                        disallow_count += 1
                    elif line.startswith('allow:'):
                        allow_count += 1
                    elif line.startswith('sitemap:'):
                        sitemap_count += 1
                
                validation["directives"] = {
                    "disallow_rules": disallow_count,
                    "allow_rules": allow_count,
                    "sitemaps": sitemap_count
                }
                validation["sitemaps_referenced"] = sitemap_count
                
                # Default to allowing crawling if no explicit disallow /
                if disallow_count == 0 or not validation["allows_crawling"]:
                    validation["allows_crawling"] = True
            else:
                validation["errors"].append(f"Robots.txt not accessible: HTTP {response['status_code']}")
        
        except Exception as e:
            validation["errors"].append(f"Robots.txt validation failed: {str(e)}")
        
        return validation
    
    def _generate_validation_recommendations(self, validation_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        
        recommendations = []
        
        # Overall pass rate
        pass_rate = validation_report["validation_summary"]["pass_rate"]
        if pass_rate < 90:
            recommendations.append(f"Low pass rate ({pass_rate:.1f}%): Address critical SEO issues")
        
        # Error distribution
        error_dist = validation_report["validation_summary"]["error_distribution"]
        if "Missing title tag" in error_dist:
            recommendations.append("Add title tags to all pages")
        if "Missing meta description" in error_dist:
            recommendations.append("Add meta descriptions to all pages")
        if "Missing H1 tag" in error_dist:
            recommendations.append("Ensure all pages have H1 tags")
        if "Missing canonical link" in error_dist:
            recommendations.append("Add canonical links to prevent duplicate content")
        
        # Performance issues
        perf_summary = validation_report["performance_metrics"]
        if perf_summary.get("response_time_distribution", {}).get("very_slow", 0) > 0:
            recommendations.append("Optimize slow-loading pages (response time > 2000ms)")
        
        # SEO compliance
        seo_compliance = validation_report["seo_compliance"]
        if seo_compliance.get("title_compliance", {}).get("found_percentage", 100) < 95:
            recommendations.append("Improve title tag coverage")
        if seo_compliance.get("meta_desc_compliance", {}).get("found_percentage", 100) < 95:
            recommendations.append("Improve meta description coverage")
        
        # Sitemap issues
        sitemap_val = validation_report["sitemap_validation"]
        if not sitemap_val.get("sitemap_accessible"):
            recommendations.append("Fix sitemap accessibility issues")
        if sitemap_val.get("url_validation", {}).get("validity_rate", 100) < 90:
            recommendations.append("Fix broken URLs in sitemap")
        
        # Robots.txt issues
        robots_val = validation_report["robots_txt_validation"]
        if not robots_val.get("robots_accessible"):
            recommendations.append("Create or fix robots.txt file")
        if not robots_val.get("allows_crawling"):
            recommendations.append("Review robots.txt disallow directives")
        
        return recommendations


# Singleton instance
page_validator = PageValidator()
