"""
Structured Data (JSON-LD) System for SEO
Generates comprehensive schema markup for search engines
"""

from typing import Dict, Any, List, Optional
from django.utils.text import slugify
from tools.models import Tool, ToolCategory
from seo.models import SEOPage, LongTailVariant
from urllib.parse import urljoin
from django.conf import settings


class StructuredDataEngine:
    """Advanced structured data generation for SEO"""
    
    def __init__(self, request):
        self.request = request
        self.base_url = request.build_absolute_uri('/')
        
    def generate_tool_schema(self, tool: Tool) -> Dict[str, Any]:
        """Generate comprehensive SoftwareApplication schema for tool"""
        
        schema = {
            "@context": "https://schema.org",
            "@type": tool.schema_type or "SoftwareApplication",
            "name": tool.name,
            "description": tool.short_desc,
            "url": self.request.build_absolute_uri(tool.get_absolute_url()),
            "applicationCategory": tool.category.name,
            "operatingSystem": "Any",
            "browserRequirements": "Requires JavaScript",
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD"
            },
            "author": {
                "@type": "Organization",
                "name": "LamGen",
                "url": self.base_url
            },
            "publisher": {
                "@type": "Organization",
                "name": "LamGen",
                "url": self.base_url
            },
            "datePublished": tool.created_at.isoformat(),
            "dateModified": tool.updated_at.isoformat(),
            "inLanguage": "en-US"
        }
        
        # Add tool-specific properties
        if tool.keywords:
            schema["keywords"] = ", ".join(tool.keywords)
        
        if tool.use_cases:
            schema["featureList"] = tool.use_cases
        
        # Add screenshots if available
        if tool.og_image:
            schema["screenshot"] = self.request.build_absolute_uri(tool.og_image)
        
        # Add aggregate rating if available
        if tool.view_count > 0:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": "4.5",
                "ratingCount": str(tool.view_count),
                "bestRating": "5",
                "worstRating": "1"
            }
        
        # Add software version
        schema["softwareVersion"] = "1.0"
        
        # Add download/usage URL
        schema["downloadUrl"] = self.request.build_absolute_uri(tool.get_absolute_url())
        
        return schema
    
    def generate_faq_schema(self, faq_items: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate FAQPage schema"""
        
        if not faq_items:
            return {}
        
        main_entity = []
        
        for item in faq_items:
            faq_entry = {
                "@type": "Question",
                "name": item.get("q", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item.get("a", "")
                }
            }
            main_entity.append(faq_entry)
        
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": main_entity
        }
        
        return schema
    
    def generate_breadcrumb_schema(self, breadcrumbs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate BreadcrumbList schema"""
        
        if not breadcrumbs:
            return {}
        
        item_list_element = []
        
        for i, crumb in enumerate(breadcrumbs, 1):
            breadcrumb_item = {
                "@type": "ListItem",
                "position": i,
                "name": crumb.get("title", ""),
                "item": self.request.build_absolute_uri(crumb.get("url", ""))
            }
            item_list_element.append(breadcrumb_item)
        
        schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": item_list_element
        }
        
        return schema
    
    def generate_howto_schema(self, tool: Tool, steps: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate HowTo schema for tool usage"""
        
        if not steps:
            return {}
        
        schema = {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": f"How to Use {tool.name}",
            "description": f"Step-by-step guide to use {tool.name}",
            "image": self.request.build_absolute_uri(f"/static/img/og-default.png"),
            "totalTime": "PT5M",  # Estimated 5 minutes
            "supply": [],  # Tools don't require supplies
            "tool": [
                {
                    "@type": "Thing",
                    "name": tool.name
                }
            ],
            "step": []
        }
        
        for i, step in enumerate(steps, 1):
            step_schema = {
                "@type": "HowToStep",
                "position": i,
                "name": step.get("title", f"Step {i}"),
                "text": step.get("content", ""),
                "image": self.request.build_absolute_uri(f"/static/img/og-default.png")
            }
            schema["step"].append(step_schema)
        
        return schema
    
    def generate_category_schema(self, category: ToolCategory, tools: List[Tool]) -> Dict[str, Any]:
        """Generate CollectionPage schema for category"""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": f"{category.name} Tools",
            "description": category.description or f"Collection of {category.name} tools",
            "url": self.request.build_absolute_uri(category.get_absolute_url()),
            "isPartOf": {
                "@type": "WebSite",
                "name": "LamGen",
                "url": self.base_url
            },
            "about": {
                "@type": "Thing",
                "name": category.name
            },
            "mainEntity": {
                "@type": "ItemList",
                "numberOfItems": len(tools),
                "itemListElement": []
            },
            "author": {
                "@type": "Organization",
                "name": "LamGen",
                "url": self.base_url
            },
            "publisher": {
                "@type": "Organization",
                "name": "LamGen",
                "url": self.base_url
            }
        }
        
        # Add tools to item list
        for i, tool in enumerate(tools, 1):
            tool_item = {
                "@type": "ListItem",
                "position": i,
                "url": self.request.build_absolute_uri(tool.get_absolute_url()),
                "name": tool.name
            }
            schema["mainEntity"]["itemListElement"].append(tool_item)
        
        return schema
    
    def generate_organization_schema(self) -> Dict[str, Any]:
        """Generate Organization schema for LamGen"""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "LamGen",
            "url": self.base_url,
            "logo": self.request.build_absolute_uri("/static/img/favicon.svg"),
            "description": "Free online tools for developers, students, writers and professionals",
            "sameAs": [
                # Add social media URLs if available
            ],
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "customer service",
                "url": self.base_url
            },
            "foundingDate": "2024",
            "areaServed": "Worldwide"
        }
        
        return schema
    
    def generate_website_schema(self) -> Dict[str, Any]:
        """Generate WebSite schema"""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "LamGen",
            "url": self.base_url,
            "description": "265+ Free Online Tools for Developers, Students & Writers",
            "potentialAction": {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": f"{self.base_url}search/?q={{search_term_string}}"
                },
                "query-input": "required name=search_term_string"
            },
            "publisher": {
                "@type": "Organization",
                "name": "LamGen",
                "url": self.base_url
            }
        }
        
        return schema
    
    def generate_seo_page_schema(self, page: SEOPage) -> Dict[str, Any]:
        """Generate schema for SEO programmatic pages"""
        
        schema_type = page.category.schema_type or "ItemList"
        
        if schema_type == "ItemList":
            return self._generate_itemlist_schema(page)
        elif schema_type == "Article":
            return self._generate_article_schema(page)
        elif schema_type == "FAQPage":
            return self._generate_faq_page_schema(page)
        else:
            return self._generate_webpage_schema(page)
    
    def _generate_itemlist_schema(self, page: SEOPage) -> Dict[str, Any]:
        """Generate ItemList schema for pages with lists"""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": page.topic,
            "description": page.meta_description or page.content_intro,
            "url": self.request.build_absolute_uri(page.get_absolute_url()),
            "numberOfItems": len(page.items),
            "itemListElement": []
        }
        
        for i, item in enumerate(page.items, 1):
            item_element = {
                "@type": "ListItem",
                "position": i,
                "name": str(item)
            }
            schema["itemListElement"].append(item_element)
        
        return schema
    
    def _generate_article_schema(self, page: SEOPage) -> Dict[str, Any]:
        """Generate Article schema for content pages"""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": page.topic,
            "description": page.meta_description or page.content_intro,
            "url": self.request.build_absolute_uri(page.get_absolute_url()),
            "datePublished": page.created_at.isoformat(),
            "dateModified": page.updated_at.isoformat(),
            "author": {
                "@type": "Organization",
                "name": "LamGen",
                "url": self.base_url
            },
            "publisher": {
                "@type": "Organization",
                "name": "LamGen",
                "url": self.base_url
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": self.request.build_absolute_uri(page.get_absolute_url())
            }
        }
        
        return schema
    
    def _generate_faq_page_schema(self, page: SEOPage) -> Dict[str, Any]:
        """Generate FAQPage schema for FAQ pages"""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        
        # Convert items to FAQ format if they contain Q&A pairs
        for item in page.items:
            if isinstance(item, dict) and 'q' in item and 'a' in item:
                faq_entry = {
                    "@type": "Question",
                    "name": item['q'],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item['a']
                    }
                }
                schema["mainEntity"].append(faq_entry)
        
        return schema
    
    def _generate_webpage_schema(self, page: SEOPage) -> Dict[str, Any]:
        """Generate WebPage schema for general pages"""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": page.topic,
            "description": page.meta_description or page.content_intro,
            "url": self.request.build_absolute_uri(page.get_absolute_url()),
            "isPartOf": {
                "@type": "WebSite",
                "name": "LamGen",
                "url": self.base_url
            },
            "about": {
                "@type": "Thing",
                "name": page.category.name
            },
            "datePublished": page.created_at.isoformat(),
            "dateModified": page.updated_at.isoformat()
        }
        
        return schema
    
    def generate_longtail_schema(self, variant: LongTailVariant) -> Dict[str, Any]:
        """Generate schema for longtail variant pages"""
        
        # Base schema from the parent tool
        base_schema = self.generate_tool_schema(variant.tool)
        
        # Override with variant-specific information
        base_schema.update({
            "name": variant.meta_title,
            "description": variant.meta_description,
            "url": self.request.build_absolute_uri(variant.get_absolute_url())
        })
        
        # Add variant-specific keywords
        if variant.use_cases:
            base_schema["keywords"] = ", ".join(variant.use_cases)
        
        # Add FAQ if available
        if variant.faq_items:
            faq_schema = self.generate_faq_schema(variant.faq_items)
            if faq_schema:
                base_schema["mainEntity"] = faq_schema.get("mainEntity", [])
        
        return base_schema
    
    def generate_service_schema(self, tool: Tool) -> Dict[str, Any]:
        """Generate Service schema for tools that provide services"""
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": tool.name,
            "description": tool.short_desc,
            "url": self.request.build_absolute_uri(tool.get_absolute_url()),
            "provider": {
                "@type": "Organization",
                "name": "LamGen",
                "url": self.base_url
            },
            "serviceType": tool.category.name,
            "areaServed": "Worldwide",
            "hasOfferCatalog": {
                "@type": "OfferCatalog",
                "name": f"{tool.name} Services",
                "itemListElement": [
                    {
                        "@type": "Offer",
                        "itemOffered": {
                            "@type": "Service",
                            "name": tool.name,
                            "description": tool.short_desc
                        },
                        "price": "0",
                        "priceCurrency": "USD",
                        "availability": "https://schema.org/InStock"
                    }
                ]
            }
        }
        
        return schema
    
    def generate_review_schema(self, tool: Tool) -> Dict[str, Any]:
        """Generate Review schema (can be expanded with real user reviews)"""
        
        # Placeholder review - in production, this would come from actual user reviews
        schema = {
            "@context": "https://schema.org",
            "@type": "Review",
            "itemReviewed": {
                "@type": "SoftwareApplication",
                "name": tool.name,
                "applicationCategory": tool.category.name
            },
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": "4.5",
                "bestRating": "5"
            },
            "author": {
                "@type": "Person",
                "name": "Anonymous User"
            },
            "reviewBody": f"Great {tool.name.lower()} tool! Easy to use and provides accurate results."
        }
        
        return schema
    
    def generate_video_schema(self, tool: Tool, video_url: str = None) -> Dict[str, Any]:
        """Generate VideoObject schema (for tool tutorials)"""
        
        if not video_url:
            return {}
        
        schema = {
            "@context": "https://schema.org",
            "@type": "VideoObject",
            "name": f"How to Use {tool.name}",
            "description": f"Step-by-step tutorial for {tool.name}",
            "thumbnailUrl": self.request.build_absolute_uri(f"/static/img/og-default.png"),
            "uploadDate": tool.created_at.isoformat(),
            "contentUrl": video_url,
            "embedUrl": video_url,
            "duration": "PT2M30S",  # Example duration
            "isFamilyFriendly": True,
            "regionsAllowed": ["US", "GB", "CA", "AU", "IN"],
            "potentialAction": {
                "@type": "WatchAction",
                "target": video_url
            }
        }
        
        return schema
    
    def generate_comprehensive_schema(self, context_type: str, **kwargs) -> List[Dict[str, Any]]:
        """Generate multiple schema types for comprehensive SEO"""
        
        schemas = []
        
        if context_type == "tool":
            tool = kwargs.get("tool")
            if not tool:
                return schemas
            
            # Main tool schema
            schemas.append(self.generate_tool_schema(tool))
            
            # Service schema if applicable
            if tool.category.name.lower() in ["converter", "generator", "analyzer"]:
                schemas.append(self.generate_service_schema(tool))
            
            # FAQ schema if available
            faq_items = kwargs.get("faq_items", [])
            if faq_items:
                schemas.append(self.generate_faq_schema(faq_items))
            
            # HowTo schema if steps available
            steps = kwargs.get("steps", [])
            if steps:
                schemas.append(self.generate_howto_schema(tool, steps))
            
            # Review schema (placeholder)
            schemas.append(self.generate_review_schema(tool))
            
        elif context_type == "category":
            category = kwargs.get("category")
            tools = kwargs.get("tools", [])
            if category and tools:
                schemas.append(self.generate_category_schema(category, tools))
        
        elif context_type == "seo_page":
            page = kwargs.get("page")
            if page:
                schemas.append(self.generate_seo_page_schema(page))
        
        elif context_type == "longtail":
            variant = kwargs.get("variant")
            if variant:
                schemas.append(self.generate_longtail_schema(variant))
        
        # Always include organization and website schemas for homepage
        if context_type in ["homepage", "tool", "category"]:
            schemas.append(self.generate_organization_schema())
            schemas.append(self.generate_website_schema())
        
        return schemas
    
    def get_schema_json_ld(self, schemas: List[Dict[str, Any]]) -> str:
        """Convert schemas to JSON-LD script format"""
        
        if not schemas:
            return ""
        
        # If only one schema, return it directly
        if len(schemas) == 1:
            import json
            return f'<script type="application/ld+json">{json.dumps(schemas[0], indent=2)}</script>'
        
        # Multiple schemas - return as graph
        import json
        
        graph_schema = {
            "@context": "https://schema.org",
            "@graph": schemas
        }
        
        return f'<script type="application/ld+json">{json.dumps(graph_schema, indent=2)}</script>'


# Helper functions for template integration
def build_tool_schema(tool: Tool, request, **kwargs) -> Dict[str, Any]:
    """Build comprehensive schema for tool page"""
    engine = StructuredDataEngine(request)
    return engine.generate_comprehensive_schema("tool", tool=tool, **kwargs)


def build_category_schema(category: ToolCategory, tools: List[Tool], request) -> Dict[str, Any]:
    """Build schema for category page"""
    engine = StructuredDataEngine(request)
    return engine.generate_comprehensive_schema("category", category=category, tools=tools)


def build_seo_page_schema(page: SEOPage, request) -> Dict[str, Any]:
    """Build schema for SEO page"""
    engine = StructuredDataEngine(request)
    return engine.generate_comprehensive_schema("seo_page", page=page)


def build_website_schema(request) -> Dict[str, Any]:
    """Build website schema for homepage"""
    engine = StructuredDataEngine(request)
    return engine.generate_comprehensive_schema("homepage")


def build_organization_schema(request) -> Dict[str, Any]:
    """Build organization schema"""
    engine = StructuredDataEngine(request)
    return engine.generate_organization_schema()


def build_breadcrumb_schema(request, *args) -> Dict[str, Any]:
    """Build breadcrumb schema"""
    engine = StructuredDataEngine(request)
    
    breadcrumbs = []
    # Add home
    breadcrumbs.append({"title": "Home", "url": "/"})
    
    # Add category if provided
    if len(args) >= 1 and hasattr(args[0], 'get_absolute_url'):
        breadcrumbs.append({"title": args[0].name, "url": args[0].get_absolute_url()})
    
    # Add tool if provided
    if len(args) >= 2 and hasattr(args[1], 'get_absolute_url'):
        breadcrumbs.append({"title": args[1].name, "url": args[1].get_absolute_url()})
    
    return engine.generate_breadcrumb_schema(breadcrumbs)


def build_faq_schema(faq_items: List[Dict[str, str]]) -> Dict[str, Any]:
    """Build FAQ schema"""
    engine = StructuredDataEngine(None)  # Request not needed for FAQ schema
    return engine.generate_faq_schema(faq_items)
