"""
Tool Ecosystem Service
Builds interconnected utility ecosystem with related tools, workflow chaining, and user retention
"""

from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Q
from django.core.cache import cache
from django.urls import reverse
from tools.models import Tool, ToolCategory
import json
import time


class ToolEcosystem:
    """Builds interconnected tool ecosystem for user retention and stickiness"""
    
    def __init__(self):
        self.cache_timeout = 60 * 30  # 30 minutes
        self.workflow_cache_timeout = 60 * 60  # 1 hour
        
    def get_related_tools(self, tool: Tool, limit: int = 8) -> List[Dict[str, Any]]:
        """Get related tools with multiple relevance signals"""
        
        cache_key = f"related_tools_{tool.id}_{limit}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        related_tools = []
        
        # 1. Category siblings (highest priority)
        category_tools = tool.category.tools.filter(is_active=True).exclude(id=tool.id)
        for related_tool in category_tools[:3]:
            related_tools.append({
                'tool': related_tool,
                'relevance_score': 0.9,
                'relationship_type': 'category_sibling',
                'reason': f'Also in {tool.category.name}'
            })
        
        # 2. Keyword overlap tools
        tool_keywords = set(tool.keywords or [])
        if tool_keywords:
            keyword_tools = Tool.objects.filter(
                is_active=True
            ).exclude(id=tool.id).exclude(category=tool.category)
            
            # Calculate keyword overlap score
            for related_tool in keyword_tools:
                related_keywords = set(related_tool.keywords or [])
                overlap = len(tool_keywords & related_keywords)
                if overlap > 0:
                    score = min(0.8, overlap / max(len(tool_keywords), len(related_keywords)))
                    if len(related_tools) < limit:
                        related_tools.append({
                            'tool': related_tool,
                            'relevance_score': score,
                            'relationship_type': 'keyword_overlap',
                            'reason': f'Shared keywords: {", ".join(list(tool_keywords & related_keywords)[:3])}'
                        })
        
        # 3. Function-based tools
        function_map = {
            'pdf': ['merge', 'split', 'compress', 'convert', 'rotate', 'watermark'],
            'json': ['formatter', 'validator', 'minifier', 'beautifier', 'converter'],
            'image': ['compress', 'resize', 'convert', 'crop', 'watermark', 'optimize'],
            'text': ['counter', 'case-converter', 'extractor', 'analyzer', 'formatter'],
            'regex': ['tester', 'generator', 'validator', 'explainer'],
            'base64': ['encoder', 'decoder', 'image-converter', 'file-converter'],
            'url': ['encoder', 'decoder', 'shortener', 'validator'],
            'color': ['converter', 'picker', 'palette-generator', 'analyzer'],
            'hash': ['generator', 'validator', 'comparator', 'cracker'],
            'cron': ['generator', 'parser', 'validator', 'explainer'],
        }
        
        # Find function-based relationships
        tool_name_lower = tool.name.lower()
        for function, related_functions in function_map.items():
            if any(func in tool_name_lower for func in related_functions):
                function_tools = Tool.objects.filter(
                    is_active=True,
                    name__icontains=related_functions[0]
                ).exclude(id=tool.id)[:2]
                
                for related_tool in function_tools:
                    if len(related_tools) < limit:
                        related_tools.append({
                            'tool': related_tool,
                            'relevance_score': 0.7,
                            'relationship_type': 'function_based',
                            'reason': f'Also handles {function} operations'
                        })
        
        # Sort by relevance score and limit
        related_tools.sort(key=lambda x: x['relevance_score'], reverse=True)
        related_tools = related_tools[:limit]
        
        # Cache result
        cache.set(cache_key, related_tools, self.cache_timeout)
        
        return related_tools
    
    def get_workflow_suggestions(self, tool: Tool, limit: int = 5) -> List[Dict[str, Any]]:
        """Get workflow suggestions for chaining tools"""
        
        cache_key = f"workflow_suggestions_{tool.id}_{limit}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Predefined workflow chains
        workflow_chains = {
            'pdf_merge': {
                'next_tools': ['pdf-compressor', 'pdf-watermarker', 'pdf-encryptor'],
                'workflow_name': 'PDF Processing Pipeline',
                'description': 'Merge → Compress → Watermark → Encrypt'
            },
            'image_processor': {
                'next_tools': ['image-compressor', 'image-converter', 'image-resizer'],
                'workflow_name': 'Image Optimization',
                'description': 'Resize → Compress → Convert Format'
            },
            'json_formatter': {
                'next_tools': ['json-validator', 'yaml-converter', 'csv-converter'],
                'workflow_name': 'Data Processing',
                'description': 'Format → Validate → Convert'
            },
            'text_analyzer': {
                'next_tools': ['word-counter', 'case-converter', 'regex-tester'],
                'workflow_name': 'Text Analysis',
                'description': 'Analyze → Count → Transform'
            },
            'base64_encoder': {
                'next_tools': ['base64-decoder', 'image-converter', 'file-converter'],
                'workflow_name': 'Encoding Pipeline',
                'description': 'Encode → Decode → Convert Format'
            },
            'color_converter': {
                'next_tools': ['color-palette', 'gradient-generator', 'css-generator'],
                'workflow_name': 'Color Design',
                'description': 'Convert → Generate Palette → Create CSS'
            },
            'hash_generator': {
                'next_tools': ['hash-validator', 'password-generator', 'salt-generator'],
                'workflow_name': 'Security Tools',
                'description': 'Generate → Validate → Strengthen'
            }
        }
        
        workflow_suggestions = []
        
        # Find matching workflow based on tool name/function
        tool_name_lower = tool.name.lower()
        
        for workflow_key, workflow_data in workflow_chains.items():
            if any(keyword in tool_name_lower for keyword in workflow_key.split('_')):
                next_tools = Tool.objects.filter(
                    is_active=True,
                    slug__in=workflow_data['next_tools']
                ).exclude(id=tool.id)[:limit]
                
                for next_tool in next_tools:
                    workflow_suggestions.append({
                        'tool': next_tool,
                        'workflow_name': workflow_data['workflow_name'],
                        'workflow_description': workflow_data['description'],
                        'relevance_score': 0.85,
                        'position': 'next'
                    })
        
        # Cache result
        cache.set(cache_key, workflow_suggestions, self.workflow_cache_timeout)
        
        return workflow_suggestions
    
    def get_people_also_use(self, tool: Tool, limit: int = 6) -> List[Dict[str, Any]]:
        """Get tools people also use based on usage patterns"""
        
        cache_key = f"people_also_use_{tool.id}_{limit}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Get tools with high usage in same category
        popular_tools = tool.category.tools.filter(
            is_active=True
        ).exclude(id=tool.id).order_by('-usage_count', '-view_count')[:limit]
        
        people_also_use = []
        for i, related_tool in enumerate(popular_tools):
            people_also_use.append({
                'tool': related_tool,
                'usage_count': related_tool.usage_count,
                'view_count': related_tool.view_count,
                'popularity_score': min(1.0, (related_tool.usage_count + related_tool.view_count) / 1000),
                'position': i + 1
            })
        
        # Cache result
        cache.set(cache_key, people_also_use, self.cache_timeout)
        
        return people_also_use
    
    def get_category_hub_data(self, category: ToolCategory) -> Dict[str, Any]:
        """Get comprehensive category hub data"""
        
        cache_key = f"category_hub_{category.id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Get category statistics
        tools = category.tools.filter(is_active=True)
        total_tools = tools.count()
        total_usage = tools.aggregate(total=models.Sum('usage_count'))['total'] or 0
        total_views = tools.aggregate(total=models.Sum('view_count'))['total'] or 0
        
        # Get featured tools
        featured_tools = tools.filter(is_featured=True).order_by('-usage_count')[:4]
        
        # Get trending tools (recent usage)
        trending_tools = tools.order_by('-usage_count', '-view_count')[:6]
        
        # Get newest tools
        newest_tools = tools.filter(is_new=True).order_by('-created_at')[:4]
        
        # Get tool subcategories based on keywords
        subcategories = self._extract_category_subcategories(tools)
        
        hub_data = {
            'category': category,
            'total_tools': total_tools,
            'total_usage': total_usage,
            'total_views': total_views,
            'featured_tools': featured_tools,
            'trending_tools': trending_tools,
            'newest_tools': newest_tools,
            'subcategories': subcategories,
            'related_categories': self._get_related_categories(category),
            'category_description': category.description or category.short_desc,
            'category_intro': category.category_intro,
            'best_use_cases': category.best_use_cases or [],
            'category_faq': category.category_faq or [],
            'seo_metadata': category.get_seo_metadata()
        }
        
        # Cache result
        cache.set(cache_key, hub_data, self.cache_timeout)
        
        return hub_data
    
    def _extract_category_subcategories(self, tools) -> List[Dict[str, Any]]:
        """Extract subcategories from tools based on keywords and patterns"""
        
        subcategories = {}
        keyword_groups = {}
        
        for tool in tools:
            tool_keywords = tool.keywords or []
            
            # Group by common keyword patterns
            for keyword in tool_keywords:
                if keyword not in keyword_groups:
                    keyword_groups[keyword] = []
                keyword_groups[keyword].append(tool)
        
        # Create subcategories from keyword groups with 3+ tools
        for keyword, grouped_tools in keyword_groups.items():
            if len(grouped_tools) >= 3:
                subcategories[keyword] = {
                    'name': keyword.title(),
                    'slug': keyword.lower().replace(' ', '-'),
                    'tools': grouped_tools[:6],  # Limit to 6 tools per subcategory
                    'count': len(grouped_tools)
                }
        
        # Sort by count and return top subcategories
        sorted_subcategories = sorted(
            subcategories.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )[:8]  # Limit to 8 subcategories
        
        return [subcat for _, subcat in sorted_subcategories]
    
    def _get_related_categories(self, category: ToolCategory) -> List[Dict[str, Any]]:
        """Get related categories based on tool relationships"""
        
        # Get tools in current category
        category_tools = category.tools.filter(is_active=True)
        category_keywords = set()
        
        for tool in category_tools:
            category_keywords.update(tool.keywords or [])
        
        # Find categories with overlapping keywords
        related_categories = []
        all_categories = ToolCategory.objects.filter(is_active=True).exclude(id=category.id)
        
        for related_cat in all_categories:
            related_tools = related_cat.tools.filter(is_active=True)
            related_keywords = set()
            
            for tool in related_tools:
                related_keywords.update(tool.keywords or [])
            
            # Calculate keyword overlap
            overlap = len(category_keywords & related_keywords)
            if overlap > 0:
                similarity_score = overlap / max(len(category_keywords), len(related_keywords))
                
                if similarity_score > 0.1:  # Minimum 10% overlap
                    related_categories.append({
                        'category': related_cat,
                        'similarity_score': similarity_score,
                        'overlapping_keywords': list(category_keywords & related_keywords)[:5],
                        'tool_count': related_tools.count()
                    })
        
        # Sort by similarity and return top 5
        related_categories.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return related_categories[:5]
    
    def get_user_session_data(self, session_key: str) -> Dict[str, Any]:
        """Get user session data for workflow and history"""
        
        session_data = cache.get(f"user_session_{session_key}") or {
            'recent_tools': [],
            'saved_workflows': [],
            'tool_history': {},
            'preferences': {},
            'session_start': time.time()
        }
        
        return session_data
    
    def update_user_session(self, session_key: str, tool: Tool, action: str = 'used'):
        """Update user session with tool usage"""
        
        session_data = self.get_user_session_data(session_key)
        
        # Add to recent tools
        if tool.id not in [t['id'] for t in session_data['recent_tools']]:
            session_data['recent_tools'].insert(0, {
                'id': tool.id,
                'name': tool.name,
                'slug': tool.slug,
                'category': tool.category.name,
                'timestamp': time.time()
            })
        
        # Keep only last 20 recent tools
        session_data['recent_tools'] = session_data['recent_tools'][:20]
        
        # Update tool history
        if tool.slug not in session_data['tool_history']:
            session_data['tool_history'][tool.slug] = {
                'usage_count': 0,
                'first_used': time.time(),
                'last_used': time.time()
            }
        
        session_data['tool_history'][tool.slug]['usage_count'] += 1
        session_data['tool_history'][tool.slug]['last_used'] = time.time()
        
        # Save session data
        cache.set(f"user_session_{session_key}", session_data, 60 * 60 * 24)  # 24 hours
        
        return session_data
    
    def get_workflow_chain(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow chain by ID"""
        
        cache_key = f"workflow_chain_{workflow_id}"
        return cache.get(cache_key)
    
    def save_workflow_chain(self, workflow_id: str, workflow_data: Dict[str, Any]):
        """Save workflow chain"""
        
        cache_key = f"workflow_chain_{workflow_id}"
        cache.set(cache_key, workflow_data, 60 * 60 * 24 * 7)  # 7 days
        
        return workflow_data
    
    def get_recommended_workflow(self, tools: List[Tool]) -> Dict[str, Any]:
        """Get recommended workflow based on used tools"""
        
        if not tools:
            return None
        
        # Analyze tool types to suggest workflow
        tool_types = []
        for tool in tools:
            tool_name_lower = tool.name.lower()
            
            if 'pdf' in tool_name_lower:
                tool_types.append('pdf')
            elif 'json' in tool_name_lower:
                tool_types.append('json')
            elif 'image' in tool_name_lower:
                tool_types.append('image')
            elif 'text' in tool_name_lower:
                tool_types.append('text')
            elif 'base64' in tool_name_lower:
                tool_types.append('base64')
            elif 'color' in tool_name_lower:
                tool_types.append('color')
        
        # Suggest workflows based on tool combinations
        workflow_suggestions = {
            ('pdf', 'image'): {
                'name': 'Document Processing',
                'description': 'Convert PDF to images or images to PDF',
                'tools': ['pdf-converter', 'image-converter', 'ocr-processor']
            },
            ('json', 'csv'): {
                'name': 'Data Conversion',
                'description': 'Convert between JSON, CSV, YAML formats',
                'tools': ['json-csv-converter', 'yaml-converter', 'data-validator']
            },
            ('text', 'regex'): {
                'name': 'Text Processing',
                'description': 'Analyze and transform text with patterns',
                'tools': ['regex-tester', 'text-analyzer', 'text-extractor']
            },
            ('base64', 'image'): {
                'name': 'Media Encoding',
                'description': 'Encode/decode images and files',
                'tools': ['base64-image-converter', 'image-optimizer', 'file-encoder']
            }
        }
        
        # Find matching workflow
        tool_types_tuple = tuple(sorted(tool_types))
        
        for workflow_key, workflow_data in workflow_suggestions.items():
            if set(tool_types_tuple).issubset(set(workflow_key)):
                return {
                    'workflow': workflow_data,
                    'confidence': len(set(tool_types_tuple)) / len(set(workflow_key)),
                    'matched_tools': tool_types
                }
        
        return None


# Singleton instance
tool_ecosystem = ToolEcosystem()
