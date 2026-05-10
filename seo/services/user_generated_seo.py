"""
User Generated SEO Implementation System
Leverages user content for maximum SEO impact through public templates, saved outputs, community examples, shared resources
"""

from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, Count, F, Avg
from django.core.cache import cache
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth.models import User
from tools.models import Tool, ToolCategory
from seo.models import SEOPage, LongTailVariant
import json
import time
from datetime import datetime, timedelta
import random


class UserGeneratedSEO:
    """User generated SEO implementation system"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 12  # 12 hours
        
        # User content types and SEO impact
        self.content_types = {
            "public_templates": {
                "seo_impact": 0.9,
                "indexable": True,
                "backlink_potential": 0.8,
                "content_multiplier": 1.5
            },
            "saved_outputs": {
                "seo_impact": 0.7,
                "indexable": True,
                "backlink_potential": 0.6,
                "content_multiplier": 1.2
            },
            "community_examples": {
                "seo_impact": 0.8,
                "indexable": True,
                "backlink_potential": 0.7,
                "content_multiplier": 1.3
            },
            "shared_resources": {
                "seo_impact": 0.85,
                "indexable": True,
                "backlink_potential": 0.75,
                "content_multiplier": 1.4
            }
        }
        
        # Quality thresholds for user content
        self.quality_thresholds = {
            "min_word_count": 150,
            "min_user_rating": 3.0,
            "min_views": 50,
            "min_downloads": 10,
            "max_reports": 2,
            "min_content_score": 0.6
        }
        
        # SEO benefits
        self.seo_benefits = {
            "indexed_pages": "Each user content becomes an indexable page",
            "backlink_targets": "User content serves as backlink targets",
            "internal_link_nodes": "User content adds to internal linking network",
            "keyword_surface": "User content expands keyword coverage",
            "content_freshness": "User content provides regular fresh content",
            "user_signals": "User engagement improves ranking signals"
        }
    
    def implement_user_generated_seo(self) -> Dict[str, Any]:
        """Implement comprehensive user generated SEO strategy"""
        
        implementation_report = {
            "implementation_timestamp": datetime.now().isoformat(),
            "content_analyzed": 0,
            "seo_pages_created": 0,
            "content_types": {},
            "quality_analysis": {},
            "seo_impact": {},
            "backlink_analysis": {},
            "keyword_expansion": {},
            "implementation_score": 0.0,
            "recommendations": [],
            "time_taken": 0
        }
        
        start_time = time.time()
        
        # Analyze user content
        user_content = self._analyze_user_content()
        implementation_report["content_analyzed"] = len(user_content)
        
        # Process different content types
        public_templates = self._process_public_templates(user_content)
        saved_outputs = self._process_saved_outputs(user_content)
        community_examples = self._process_community_examples(user_content)
        shared_resources = self._process_shared_resources(user_content)
        
        implementation_report["content_types"] = {
            "public_templates": public_templates,
            "saved_outputs": saved_outputs,
            "community_examples": community_examples,
            "shared_resources": shared_resources
        }
        
        # Analyze content quality
        quality_analysis = self._analyze_content_quality(implementation_report["content_types"])
        implementation_report["quality_analysis"] = quality_analysis
        
        # Calculate SEO impact
        seo_impact = self._calculate_seo_impact(implementation_report["content_types"])
        implementation_report["seo_impact"] = seo_impact
        
        # Analyze backlink potential
        backlink_analysis = self._analyze_backlink_potential(implementation_report["content_types"])
        implementation_report["backlink_analysis"] = backlink_analysis
        
        # Analyze keyword expansion
        keyword_expansion = self._analyze_keyword_expansion(implementation_report["content_types"])
        implementation_report["keyword_expansion"] = keyword_expansion
        
        # Calculate total SEO pages created
        total_seo_pages = sum(len(content.get("seo_pages", [])) for content in implementation_report["content_types"].values())
        implementation_report["seo_pages_created"] = total_seo_pages
        
        # Calculate implementation score
        implementation_report["implementation_score"] = self._calculate_implementation_score(implementation_report)
        
        # Generate recommendations
        implementation_report["recommendations"] = self._generate_user_seo_recommendations(implementation_report)
        
        end_time = time.time()
        implementation_report["time_taken"] = end_time - start_time
        
        # Cache results
        cache.set("user_generated_seo", implementation_report, self.cache_timeout)
        
        return implementation_report
    
    def _analyze_user_content(self) -> List[Dict[str, Any]]:
        """Analyze existing user content"""
        
        user_content = []
        
        # Simulate user content analysis
        # In production, this would query actual user-generated content tables
        
        # Generate sample public templates
        for i in range(50):
            template = {
                "id": f"template_{i}",
                "type": "public_template",
                "title": f"Professional Resume Template {i+1}",
                "content": f"This is a professional resume template with modern design...",
                "author_id": random.randint(1, 100),
                "views": random.randint(100, 5000),
                "downloads": random.randint(50, 1000),
                "rating": round(random.uniform(2.5, 5.0), 1),
                "word_count": random.randint(200, 800),
                "created_at": datetime.now() - timedelta(days=random.randint(1, 365)),
                "category": random.choice(["Resume", "CV", "Bio", "Cover Letter"]),
                "tags": random.sample(["professional", "modern", "creative", "simple", "executive", "entry-level"], 3),
                "is_public": True,
                "is_featured": random.random() < 0.1,
                "reports": random.randint(0, 5)
            }
            user_content.append(template)
        
        # Generate sample saved outputs
        for i in range(100):
            output = {
                "id": f"output_{i}",
                "type": "saved_output",
                "title": f"Generated Resume - {random.choice(['Marketing Manager', 'Software Engineer', 'Teacher', 'Sales Rep'])}",
                "content": f"John Doe\nSoftware Engineer\nSummary: Experienced software engineer with 5+ years...",
                "author_id": random.randint(1, 100),
                "views": random.randint(50, 1000),
                "downloads": random.randint(20, 500),
                "rating": round(random.uniform(3.0, 5.0), 1),
                "word_count": random.randint(150, 600),
                "created_at": datetime.now() - timedelta(days=random.randint(1, 180)),
                "category": random.choice(["Resume", "CV", "Bio"]),
                "tags": random.sample(["generated", "example", "sample", "template", "professional"], 2),
                "is_public": random.random() < 0.7,
                "is_featured": random.random() < 0.05,
                "reports": random.randint(0, 3)
            }
            user_content.append(output)
        
        # Generate sample community examples
        for i in range(75):
            example = {
                "id": f"example_{i}",
                "type": "community_example",
                "title": f"Real Resume Example - {random.choice(['Tech Startup', 'Fortune 500', 'Non-Profit', 'Government'])}",
                "content": f"Jane Smith\nSenior Product Manager\nTech Startup Experience\n\nProfessional Summary: Innovative product manager...",
                "author_id": random.randint(1, 100),
                "views": random.randint(200, 3000),
                "downloads": random.randint(100, 800),
                "rating": round(random.uniform(3.5, 5.0), 1),
                "word_count": random.randint(300, 1000),
                "created_at": datetime.now() - timedelta(days=random.randint(1, 270)),
                "category": random.choice(["Resume", "CV", "Bio", "Cover Letter"]),
                "tags": random.sample(["real", "example", "success", "career-change", "promotion"], 3),
                "is_public": True,
                "is_featured": random.random() < 0.15,
                "reports": random.randint(0, 2)
            }
            user_content.append(example)
        
        # Generate sample shared resources
        for i in range(25):
            resource = {
                "id": f"resource_{i}",
                "type": "shared_resource",
                "title": f"Ultimate {random.choice(['Resume Writing', 'CV Creation', 'Bio Writing'])} Guide",
                "content": f"Complete guide to writing professional documents. Chapter 1: Understanding the purpose...",
                "author_id": random.randint(1, 100),
                "views": random.randint(500, 5000),
                "downloads": random.randint(200, 1500),
                "rating": round(random.uniform(4.0, 5.0), 1),
                "word_count": random.randint(800, 2500),
                "created_at": datetime.now() - timedelta(days=random.randint(1, 400)),
                "category": random.choice(["Resume", "CV", "Bio", "Career Guide"]),
                "tags": random.sample(["guide", "comprehensive", "tips", "best-practices", "tutorial"], 3),
                "is_public": True,
                "is_featured": random.random() < 0.2,
                "reports": random.randint(0, 1)
            }
            user_content.append(resource)
        
        return user_content
    
    def _process_public_templates(self, user_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process public templates for SEO"""
        
        templates = [content for content in user_content if content["type"] == "public_template"]
        
        processed_templates = {
            "total_count": len(templates),
            "quality_approved": [],
            "seo_pages": [],
            "backlink_targets": [],
            "keyword_coverage": set()
        }
        
        for template in templates:
            # Quality check
            if self._meets_quality_thresholds(template):
                processed_templates["quality_approved"].append(template)
                
                # Create SEO page
                seo_page = self._create_template_seo_page(template)
                processed_templates["seo_pages"].append(seo_page)
                
                # Add as backlink target
                backlink_target = self._create_backlink_target(template, "template")
                processed_templates["backlink_targets"].append(backlink_target)
                
                # Extract keywords
                keywords = self._extract_keywords(template)
                processed_templates["keyword_coverage"].update(keywords)
        
        processed_templates["keyword_coverage"] = list(processed_templates["keyword_coverage"])
        
        return processed_templates
    
    def _process_saved_outputs(self, user_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process saved outputs for SEO"""
        
        outputs = [content for content in user_content if content["type"] == "saved_output"]
        
        processed_outputs = {
            "total_count": len(outputs),
            "quality_approved": [],
            "seo_pages": [],
            "backlink_targets": [],
            "keyword_coverage": set()
        }
        
        for output in outputs:
            # Quality check
            if self._meets_quality_thresholds(output):
                processed_outputs["quality_approved"].append(output)
                
                # Create SEO page
                seo_page = self._create_output_seo_page(output)
                processed_outputs["seo_pages"].append(seo_page)
                
                # Add as backlink target
                backlink_target = self._create_backlink_target(output, "output")
                processed_outputs["backlink_targets"].append(backlink_target)
                
                # Extract keywords
                keywords = self._extract_keywords(output)
                processed_outputs["keyword_coverage"].update(keywords)
        
        processed_outputs["keyword_coverage"] = list(processed_outputs["keyword_coverage"])
        
        return processed_outputs
    
    def _process_community_examples(self, user_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process community examples for SEO"""
        
        examples = [content for content in user_content if content["type"] == "community_example"]
        
        processed_examples = {
            "total_count": len(examples),
            "quality_approved": [],
            "seo_pages": [],
            "backlink_targets": [],
            "keyword_coverage": set()
        }
        
        for example in examples:
            # Quality check
            if self._meets_quality_thresholds(example):
                processed_examples["quality_approved"].append(example)
                
                # Create SEO page
                seo_page = self._create_example_seo_page(example)
                processed_examples["seo_pages"].append(seo_page)
                
                # Add as backlink target
                backlink_target = self._create_backlink_target(example, "example")
                processed_examples["backlink_targets"].append(backlink_target)
                
                # Extract keywords
                keywords = self._extract_keywords(example)
                processed_examples["keyword_coverage"].update(keywords)
        
        processed_examples["keyword_coverage"] = list(processed_examples["keyword_coverage"])
        
        return processed_examples
    
    def _process_shared_resources(self, user_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process shared resources for SEO"""
        
        resources = [content for content in user_content if content["type"] == "shared_resource"]
        
        processed_resources = {
            "total_count": len(resources),
            "quality_approved": [],
            "seo_pages": [],
            "backlink_targets": [],
            "keyword_coverage": set()
        }
        
        for resource in resources:
            # Quality check
            if self._meets_quality_thresholds(resource):
                processed_resources["quality_approved"].append(resource)
                
                # Create SEO page
                seo_page = self._create_resource_seo_page(resource)
                processed_resources["seo_pages"].append(seo_page)
                
                # Add as backlink target
                backlink_target = self._create_backlink_target(resource, "resource")
                processed_resources["backlink_targets"].append(backlink_target)
                
                # Extract keywords
                keywords = self._extract_keywords(resource)
                processed_resources["keyword_coverage"].update(keywords)
        
        processed_resources["keyword_coverage"] = list(processed_resources["keyword_coverage"])
        
        return processed_resources
    
    def _meets_quality_thresholds(self, content: Dict[str, Any]) -> bool:
        """Check if content meets quality thresholds"""
        
        # Word count check
        if content["word_count"] < self.quality_thresholds["min_word_count"]:
            return False
        
        # Rating check
        if content["rating"] < self.quality_thresholds["min_user_rating"]:
            return False
        
        # Views check
        if content["views"] < self.quality_thresholds["min_views"]:
            return False
        
        # Downloads check
        if content["downloads"] < self.quality_thresholds["min_downloads"]:
            return False
        
        # Reports check
        if content["reports"] > self.quality_thresholds["max_reports"]:
            return False
        
        # Content score check
        content_score = self._calculate_content_score(content)
        if content_score < self.quality_thresholds["min_content_score"]:
            return False
        
        return True
    
    def _calculate_content_score(self, content: Dict[str, Any]) -> float:
        """Calculate overall content score"""
        
        score = 0.0
        
        # Rating contribution (40%)
        rating_score = content["rating"] / 5.0  # Normalize to 0-1
        score += rating_score * 0.4
        
        # Views contribution (20%)
        views_score = min(content["views"] / 1000, 1.0)  # Normalize to 0-1
        score += views_score * 0.2
        
        # Downloads contribution (20%)
        downloads_score = min(content["downloads"] / 500, 1.0)  # Normalize to 0-1
        score += downloads_score * 0.2
        
        # Word count contribution (10%)
        word_count_score = min(content["word_count"] / 500, 1.0)  # Normalize to 0-1
        score += word_count_score * 0.1
        
        # Engagement contribution (10%)
        engagement_score = (len(content.get("tags", [])) / 5)  # Normalize to 0-1
        score += engagement_score * 0.1
        
        return min(score, 1.0)
    
    def _create_template_seo_page(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Create SEO page for template"""
        
        seo_page = {
            "type": "user_template",
            "url": f"/templates/{template['id']}/{slugify(template['title'])}",
            "title": f"{template['title']} - Free Template",
            "meta_title": f"{template['title']} - Professional Template | LamGen",
            "meta_description": f"Download {template['title']}. Professional template with {template['downloads']} downloads and {template['rating']}/5 rating.",
            "content": template["content"],
            "author": template["author_id"],
            "category": template["category"],
            "tags": template["tags"],
            "stats": {
                "views": template["views"],
                "downloads": template["downloads"],
                "rating": template["rating"]
            },
            "schema_type": "CreativeWork",
            "canonical_url": f"https://lamgen.com/templates/{template['id']}/",
            "internal_links": self._generate_template_internal_links(template),
            "backlink_potential": self.content_types["public_templates"]["backlink_potential"]
        }
        
        return seo_page
    
    def _create_output_seo_page(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Create SEO page for saved output"""
        
        seo_page = {
            "type": "user_output",
            "url": f"/examples/{output['id']}/{slugify(output['title'])}",
            "title": f"{output['title']} - Generated Example",
            "meta_title": f"{output['title']} - Generated Resume Example | LamGen",
            "meta_description": f"View {output['title']}. Generated resume example with {output['views']} views and {output['rating']}/5 rating.",
            "content": output["content"],
            "author": output["author_id"],
            "category": output["category"],
            "tags": output["tags"],
            "stats": {
                "views": output["views"],
                "downloads": output["downloads"],
                "rating": output["rating"]
            },
            "schema_type": "Article",
            "canonical_url": f"https://lamgen.com/examples/{output['id']}/",
            "internal_links": self._generate_output_internal_links(output),
            "backlink_potential": self.content_types["saved_outputs"]["backlink_potential"]
        }
        
        return seo_page
    
    def _create_example_seo_page(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """Create SEO page for community example"""
        
        seo_page = {
            "type": "user_example",
            "url": f"/community/{example['id']}/{slugify(example['title'])}",
            "title": f"{example['title']} - Community Example",
            "meta_title": f"{example['title']} - Real Resume Example | LamGen",
            "meta_description": f"See {example['title']}. Real resume example from community with {example['views']} views and {example['rating']}/5 rating.",
            "content": example["content"],
            "author": example["author_id"],
            "category": example["category"],
            "tags": example["tags"],
            "stats": {
                "views": example["views"],
                "downloads": example["downloads"],
                "rating": example["rating"]
            },
            "schema_type": "Article",
            "canonical_url": f"https://lamgen.com/community/{example['id']}/",
            "internal_links": self._generate_example_internal_links(example),
            "backlink_potential": self.content_types["community_examples"]["backlink_potential"]
        }
        
        return seo_page
    
    def _create_resource_seo_page(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Create SEO page for shared resource"""
        
        seo_page = {
            "type": "user_resource",
            "url": f"/resources/{resource['id']}/{slugify(resource['title'])}",
            "title": f"{resource['title']} - Free Guide",
            "meta_title": f"{resource['title']} - Complete Guide | LamGen",
            "meta_description": f"Read {resource['title']}. Comprehensive guide with {resource['word_count']} words, {resource['views']} views, and {resource['rating']}/5 rating.",
            "content": resource["content"],
            "author": resource["author_id"],
            "category": resource["category"],
            "tags": resource["tags"],
            "stats": {
                "views": resource["views"],
                "downloads": resource["downloads"],
                "rating": resource["rating"]
            },
            "schema_type": "Article",
            "canonical_url": f"https://lamgen.com/resources/{resource['id']}/",
            "internal_links": self._generate_resource_internal_links(resource),
            "backlink_potential": self.content_types["shared_resources"]["backlink_potential"]
        }
        
        return seo_page
    
    def _create_backlink_target(self, content: Dict[str, Any], content_type: str) -> Dict[str, Any]:
        """Create backlink target for content"""
        
        backlink_target = {
            "url": f"/{content_type}s/{content['id']}/{slugify(content['title'])}",
            "title": content["title"],
            "content_type": content_type,
            "authority_score": self._calculate_backlink_authority(content),
            "target_audiences": self._identify_target_audiences(content),
            "linkable_assets": self._identify_linkable_assets(content),
            "outreach_potential": self._assess_outreach_potential(content)
        }
        
        return backlink_target
    
    def _calculate_backlink_authority(self, content: Dict[str, Any]) -> float:
        """Calculate backlink authority score"""
        
        authority = 50.0  # Base authority
        
        # Add for high rating
        if content["rating"] >= 4.5:
            authority += 20
        elif content["rating"] >= 4.0:
            authority += 10
        
        # Add for high views
        if content["views"] >= 1000:
            authority += 15
        elif content["views"] >= 500:
            authority += 8
        
        # Add for high downloads
        if content["downloads"] >= 500:
            authority += 10
        elif content["downloads"] >= 200:
            authority += 5
        
        # Add for content quality
        content_score = self._calculate_content_score(content)
        authority += content_score * 15
        
        # Add for featured status
        if content.get("is_featured"):
            authority += 10
        
        return min(authority, 100)
    
    def _identify_target_audiences(self, content: Dict[str, Any]) -> List[str]:
        """Identify target audiences for backlink outreach"""
        
        audiences = []
        
        category = content.get("category", "").lower()
        title = content.get("title", "").lower()
        tags = [tag.lower() for tag in content.get("tags", [])]
        
        if "resume" in category or "resume" in title:
            audiences.extend(["job_seekers", "career_changers", "students", "professionals"])
        
        if "cv" in category or "cv" in title:
            audiences.extend(["academics", "researchers", "international_professionals"])
        
        if "bio" in category or "bio" in title:
            audiences.extend(["freelancers", "consultants", "speakers", "authors"])
        
        if "teacher" in title or "education" in tags:
            audiences.append("educators")
        
        if "software" in title or "tech" in tags:
            audiences.append("tech_professionals")
        
        if "marketing" in title or "sales" in tags:
            audiences.append("marketing_professionals")
        
        return list(set(audiences))
    
    def _identify_linkable_assets(self, content: Dict[str, Any]) -> List[str]:
        """Identify linkable assets in content"""
        
        assets = []
        
        # Content type specific assets
        if content["type"] == "public_template":
            assets.extend(["downloadable_template", "preview_image", "usage_guide"])
        elif content["type"] == "saved_output":
            assets.extend(["generated_example", "success_story", "before_after"])
        elif content["type"] == "community_example":
            assets.extend(["real_case_study", "expert_insights", "career_trajectory"])
        elif content["type"] == "shared_resource":
            assets.extend(["comprehensive_guide", "checklist", "tips_tricks"])
        
        # Quality-based assets
        if content["rating"] >= 4.5:
            assets.append("highly_rated_content")
        
        if content["views"] >= 1000:
            assets.append("popular_content")
        
        if content.get("is_featured"):
            assets.append("featured_content")
        
        return assets
    
    def _assess_outreach_potential(self, content: Dict[str, Any]) -> str:
        """Assess outreach potential"""
        
        potential_score = 0
        
        # High rating
        if content["rating"] >= 4.5:
            potential_score += 2
        
        # High engagement
        if content["views"] >= 1000 and content["downloads"] >= 500:
            potential_score += 2
        
        # Featured status
        if content.get("is_featured"):
            potential_score += 1
        
        # Content quality
        if self._calculate_content_score(content) >= 0.8:
            potential_score += 1
        
        if potential_score >= 4:
            return "high"
        elif potential_score >= 2:
            return "medium"
        else:
            return "low"
    
    def _extract_keywords(self, content: Dict[str, Any]) -> List[str]:
        """Extract keywords from content"""
        
        keywords = set()
        
        # Add category as keyword
        if content.get("category"):
            keywords.add(content["category"].lower())
        
        # Add tags as keywords
        for tag in content.get("tags", []):
            keywords.add(tag.lower())
        
        # Extract from title
        title_words = content.get("title", "").lower().split()
        keywords.update([word for word in title_words if len(word) > 3])
        
        # Extract from content (sample)
        content_sample = content.get("content", "").lower()[:200]  # First 200 chars
        content_words = content_sample.split()
        keywords.update([word for word in content_words if len(word) > 4])
        
        # Add common related keywords
        category = content.get("category", "").lower()
        if "resume" in category:
            keywords.update(["resume writing", "cv writing", "professional resume", "resume template", "resume format"])
        elif "cv" in category:
            keywords.update(["curriculum vitae", "academic cv", "professional cv", "cv template"])
        elif "bio" in category:
            keywords.update(["professional bio", "personal bio", "biography writing", "bio template"])
        
        return list(keywords)
    
    def _generate_template_internal_links(self, template: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate internal links for template page"""
        
        links = []
        
        # Link to category page
        if template.get("category"):
            links.append({
                "url": f"/category/{slugify(template['category'])}/",
                "anchor": f"More {template['category']} Templates",
                "type": "navigational"
            })
        
        # Link to related templates
        links.append({
            "url": "/templates/popular/",
            "anchor": "Popular Templates",
            "type": "related"
        })
        
        # Link to main tool
        links.append({
            "url": "/resume-builder/",
            "anchor": "Create Your Resume",
            "type": "contextual"
        })
        
        return links
    
    def _generate_output_internal_links(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate internal links for output page"""
        
        links = []
        
        # Link to category page
        if output.get("category"):
            links.append({
                "url": f"/category/{slugify(output['category'])}/",
                "anchor": f"More {output['category']} Examples",
                "type": "navigational"
            })
        
        # Link to tool
        links.append({
            "url": "/resume-builder/",
            "anchor": "Create Similar Resume",
            "type": "contextual"
        })
        
        # Link to community
        links.append({
            "url": "/community/",
            "anchor": "Community Examples",
            "type": "related"
        })
        
        return links
    
    def _generate_example_internal_links(self, example: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate internal links for example page"""
        
        links = []
        
        # Link to category page
        if example.get("category"):
            links.append({
                "url": f"/category/{slugify(example['category'])}/",
                "anchor": f"More {example['category']} Examples",
                "type": "navigational"
            })
        
        # Link to community
        links.append({
            "url": "/community/",
            "anchor": "More Community Examples",
            "type": "related"
        })
        
        # Link to tool
        links.append({
            "url": "/resume-builder/",
            "anchor": "Create Your Resume",
            "type": "contextual"
        })
        
        return links
    
    def _generate_resource_internal_links(self, resource: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate internal links for resource page"""
        
        links = []
        
        # Link to category page
        if resource.get("category"):
            links.append({
                "url": f"/category/{slugify(resource['category'])}/",
                "anchor": f"More {resource['category']} Resources",
                "type": "navigational"
            })
        
        # Link to resources hub
        links.append({
            "url": "/resources/",
            "anchor": "All Resources",
            "type": "related"
        })
        
        # Link to relevant tool
        links.append({
            "url": "/resume-builder/",
            "anchor": "Apply These Tips",
            "type": "contextual"
        })
        
        return links
    
    def _analyze_content_quality(self, content_types: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content quality across types"""
        
        quality_analysis = {
            "total_content": 0,
            "quality_approved": 0,
            "approval_rate": 0.0,
            "type_breakdown": {},
            "quality_metrics": {}
        }
        
        total_content = 0
        total_approved = 0
        
        for content_type, data in content_types.items():
            type_count = data.get("total_count", 0)
            approved_count = len(data.get("quality_approved", []))
            
            total_content += type_count
            total_approved += approved_count
            
            quality_analysis["type_breakdown"][content_type] = {
                "total": type_count,
                "approved": approved_count,
                "approval_rate": (approved_count / type_count * 100) if type_count > 0 else 0
            }
        
        quality_analysis["total_content"] = total_content
        quality_analysis["quality_approved"] = total_approved
        quality_analysis["approval_rate"] = (total_approved / total_content * 100) if total_content > 0 else 0
        
        # Calculate quality metrics
        all_approved = []
        for data in content_types.values():
            all_approved.extend(data.get("quality_approved", []))
        
        if all_approved:
            ratings = [content["rating"] for content in all_approved]
            views = [content["views"] for content in all_approved]
            downloads = [content["downloads"] for content in all_approved]
            
            quality_analysis["quality_metrics"] = {
                "average_rating": sum(ratings) / len(ratings),
                "average_views": sum(views) / len(views),
                "average_downloads": sum(downloads) / len(downloads),
                "high_rated_content": len([r for r in ratings if r >= 4.5]),
                "popular_content": len([v for v in views if v >= 1000])
            }
        
        return quality_analysis
    
    def _calculate_seo_impact(self, content_types: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate SEO impact of user content"""
        
        seo_impact = {
            "total_seo_pages": 0,
            "indexable_pages": 0,
            "backlink_targets": 0,
            "keyword_coverage": set(),
            "content_freshness": {},
            "user_signals": {},
            "impact_score": 0.0
        }
        
        total_seo_pages = 0
        total_backlink_targets = 0
        all_keywords = set()
        
        for content_type, data in content_types.items():
            seo_pages = data.get("seo_pages", [])
            backlink_targets = data.get("backlink_targets", [])
            keywords = data.get("keyword_coverage", [])
            
            total_seo_pages += len(seo_pages)
            total_backlink_targets += len(backlink_targets)
            all_keywords.update(keywords)
        
        seo_impact["total_seo_pages"] = total_seo_pages
        seo_impact["indexable_pages"] = total_seo_pages  # All SEO pages are indexable
        seo_impact["backlink_targets"] = total_backlink_targets
        seo_impact["keyword_coverage"] = list(all_keywords)
        
        # Calculate content freshness
        all_content = []
        for data in content_types.values():
            all_content.extend(data.get("quality_approved", []))
        
        if all_content:
            ages = [(datetime.now() - content["created_at"]).days for content in all_content]
            seo_impact["content_freshness"] = {
                "average_age_days": sum(ages) / len(ages),
                "fresh_content": len([age for age in ages if age <= 30]),
                "recent_content": len([age for age in ages if age <= 90])
            }
        
        # Calculate user signals
        if all_content:
            total_views = sum(content["views"] for content in all_content)
            total_downloads = sum(content["downloads"] for content in all_content)
            total_ratings = sum(content["rating"] for content in all_content)
            
            seo_impact["user_signals"] = {
                "total_views": total_views,
                "total_downloads": total_downloads,
                "average_rating": total_ratings / len(all_content),
                "engagement_score": (total_views + total_downloads * 2) / len(all_content)
            }
        
        # Calculate impact score
        impact_score = 0.0
        impact_score += min(total_seo_pages / 100, 30)  # Max 30 points for pages
        impact_score += min(total_backlink_targets / 50, 25)  # Max 25 points for backlinks
        impact_score += min(len(all_keywords) / 200, 20)  # Max 20 points for keywords
        impact_score += min(seo_impact["user_signals"].get("engagement_score", 0) / 100, 25)  # Max 25 points for engagement
        
        seo_impact["impact_score"] = impact_score
        
        return seo_impact
    
    def _analyze_backlink_potential(self, content_types: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze backlink potential"""
        
        backlink_analysis = {
            "total_targets": 0,
            "high_authority_targets": 0,
            "target_audiences": set(),
            "linkable_assets": {},
            "outreach_potential": {}
        }
        
        all_targets = []
        all_audiences = set()
        all_assets = []
        
        for data in content_types.values():
            targets = data.get("backlink_targets", [])
            all_targets.extend(targets)
            
            for target in targets:
                all_audiences.update(target.get("target_audiences", []))
                all_assets.extend(target.get("linkable_assets", []))
        
        backlink_analysis["total_targets"] = len(all_targets)
        backlink_analysis["high_authority_targets"] = len([t for t in all_targets if t.get("authority_score", 0) >= 80])
        backlink_analysis["target_audiences"] = list(all_audiences)
        
        # Count linkable assets
        asset_counts = {}
        for asset in all_assets:
            asset_counts[asset] = asset_counts.get(asset, 0) + 1
        
        backlink_analysis["linkable_assets"] = asset_counts
        
        # Outreach potential
        outreach_counts = {"high": 0, "medium": 0, "low": 0}
        for target in all_targets:
            potential = target.get("outreach_potential", "low")
            outreach_counts[potential] = outreach_counts.get(potential, 0) + 1
        
        backlink_analysis["outreach_potential"] = outreach_counts
        
        return backlink_analysis
    
    def _analyze_keyword_expansion(self, content_types: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze keyword expansion"""
        
        keyword_expansion = {
            "total_keywords": 0,
            "unique_keywords": set(),
            "keyword_categories": {},
            "longtail_keywords": [],
            "commercial_keywords": [],
            "informational_keywords": []
        }
        
        all_keywords = set()
        
        for data in content_types.values():
            keywords = data.get("keyword_coverage", [])
            all_keywords.update(keywords)
        
        keyword_expansion["total_keywords"] = len(all_keywords)
        keyword_expansion["unique_keywords"] = list(all_keywords)
        
        # Categorize keywords
        for keyword in all_keywords:
            if len(keyword.split()) > 3:
                keyword_expansion["longtail_keywords"].append(keyword)
            elif any(term in keyword for term in ["template", "download", "free", "professional"]):
                keyword_expansion["commercial_keywords"].append(keyword)
            elif any(term in keyword for term in ["guide", "how", "tips", "example"]):
                keyword_expansion["informational_keywords"].append(keyword)
        
        return keyword_expansion
    
    def _calculate_implementation_score(self, implementation_report: Dict[str, Any]) -> float:
        """Calculate overall implementation score"""
        
        score = 100.0
        
        # Deduct for low approval rate
        approval_rate = implementation_report["quality_analysis"]["approval_rate"]
        if approval_rate < 70:
            score -= 20
        elif approval_rate < 85:
            score -= 10
        
        # Deduct for low SEO impact
        impact_score = implementation_report["seo_impact"]["impact_score"]
        if impact_score < 50:
            score -= 20
        elif impact_score < 70:
            score -= 10
        
        # Deduct for low backlink potential
        total_targets = implementation_report["backlink_analysis"]["total_targets"]
        if total_targets < 50:
            score -= 15
        elif total_targets < 100:
            score -= 5
        
        # Bonus for high keyword coverage
        keyword_count = implementation_report["keyword_expansion"]["total_keywords"]
        if keyword_count > 500:
            score += 10
        elif keyword_count > 300:
            score += 5
        
        return max(score, 0)
    
    def _generate_user_seo_recommendations(self, implementation_report: Dict[str, Any]) -> List[str]:
        """Generate user generated SEO recommendations"""
        
        recommendations = []
        
        # Overall score recommendations
        score = implementation_report["implementation_score"]
        
        if score < 70:
            recommendations.append("Critical improvements needed for user generated SEO")
        elif score < 85:
            recommendations.append("Several optimizations recommended for user content")
        else:
            recommendations.append("Good user generated SEO implementation - maintain current strategy")
        
        # Quality recommendations
        approval_rate = implementation_report["quality_analysis"]["approval_rate"]
        if approval_rate < 80:
            recommendations.append("Improve content quality standards to increase approval rate")
        
        # SEO impact recommendations
        impact_score = implementation_report["seo_impact"]["impact_score"]
        if impact_score < 60:
            recommendations.append("Increase SEO impact by promoting higher quality user content")
        
        # Backlink recommendations
        total_targets = implementation_report["backlink_analysis"]["total_targets"]
        if total_targets < 100:
            recommendations.append("Encourage more user content creation to increase backlink targets")
        
        # Keyword recommendations
        keyword_count = implementation_report["keyword_expansion"]["total_keywords"]
        if keyword_count < 300:
            recommendations.append("Expand keyword coverage through diverse user content")
        
        return recommendations
    
    def get_user_seo_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive user generated SEO dashboard"""
        
        dashboard = {
            "summary": {},
            "content_analysis": {},
            "seo_impact": {},
            "backlink_analysis": {},
            "keyword_analysis": {},
            "recommendations": []
        }
        
        # Get latest implementation data
        implementation_data = cache.get("user_generated_seo")
        if not implementation_data:
            implementation_data = self.implement_user_generated_seo()
        
        # Summary metrics
        dashboard["summary"] = {
            "total_content": implementation_data["content_analyzed"],
            "quality_approved": implementation_data["quality_analysis"]["quality_approved"],
            "seo_pages_created": implementation_data["seo_pages_created"],
            "implementation_score": implementation_data["implementation_score"],
            "approval_rate": implementation_data["quality_analysis"]["approval_rate"]
        }
        
        # Content analysis
        dashboard["content_analysis"] = implementation_data["quality_analysis"]
        
        # SEO impact
        dashboard["seo_impact"] = implementation_data["seo_impact"]
        
        # Backlink analysis
        dashboard["backlink_analysis"] = implementation_data["backlink_analysis"]
        
        # Keyword analysis
        dashboard["keyword_analysis"] = implementation_data["keyword_expansion"]
        
        # Recommendations
        dashboard["recommendations"] = implementation_data["recommendations"]
        
        return dashboard


# Singleton instance
user_generated_seo = UserGeneratedSEO()
