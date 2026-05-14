"""
Base Tool Framework - Unified Architecture for LamGen Tools Ecosystem

This module provides the foundational architecture for all tools in LamGen,
ensuring consistent behavior, validation, error handling, and production readiness.
"""

import json
import logging
import traceback
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction

from apps.tools.models import Tool, ToolUsageHistory
from apps.tools.utils.validation import ValidationFramework
from apps.tools.utils.rate_limit import RateLimiter
from apps.tools.utils.analytics import AnalyticsTracker

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Tool execution status codes"""
    SUCCESS = "success"
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMITED = "rate_limited"
    PROCESSING = "processing"


@dataclass
class ToolResult:
    """Standardized result structure for all tool operations"""
    status: ToolStatus
    data: Any = None
    error_message: str = ""
    validation_errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'data': self.data,
            'error_message': self.error_message,
            'validation_errors': self.validation_errors,
            'metadata': self.metadata,
            'processing_time_ms': self.processing_time_ms
        }
    
    def to_json_response(self) -> JsonResponse:
        """Convert to Django JsonResponse with appropriate status code"""
        status_code = 200 if self.status == ToolStatus.SUCCESS else 400
        if self.status == ToolStatus.RATE_LIMITED:
            status_code = 429
        return JsonResponse(self.to_dict(), status=status_code)


@dataclass
class ToolConfig:
    """Configuration structure for tool metadata and behavior"""
    name: str
    slug: str
    category: str
    description: str
    version: str = "1.0.0"
    requires_auth: bool = False
    rate_limit_per_minute: int = 60
    max_file_size_mb: int = 10
    supported_formats: List[str] = field(default_factory=list)
    ai_enhanced: bool = False
    cache_ttl_seconds: int = 300
    seo_metadata: Dict[str, str] = field(default_factory=dict)


class BaseTool(ABC):
    """
    Abstract base class for all LamGen tools.
    
    All tools must inherit from this class and implement the required methods.
    This ensures consistent behavior, validation, error handling, and production readiness.
    """
    
    def __init__(self, config: ToolConfig):
        self.config = config
        self.validator = ValidationFramework()
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)
        self.analytics = AnalyticsTracker()
        
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """
        Main processing logic for the tool.
        Must be implemented by each specific tool.
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for input validation.
        Defines expected input structure and constraints.
        """
        pass
    
    def validate_input(self, input_data: Dict[str, Any]) -> List[str]:
        """
        Validate input data against schema.
        Override for custom validation logic.
        """
        return self.validator.validate(input_data, self.get_schema())
    
    def get_cache_key(self, input_data: Dict[str, Any]) -> str:
        """Generate cache key for input data"""
        import hashlib
        import json
        data_str = json.dumps(input_data, sort_keys=True)
        return f"tool:{self.config.slug}:{hashlib.md5(data_str.encode()).hexdigest()}"
    
    def get_cached_result(self, input_data: Dict[str, Any]) -> Optional[ToolResult]:
        """Retrieve cached result if available"""
        cache_key = self.get_cache_key(input_data)
        cached_data = cache.get(cache_key)
        if cached_data:
            return ToolResult(**cached_data)
        return None
    
    def cache_result(self, input_data: Dict[str, Any], result: ToolResult) -> None:
        """Cache successful results"""
        if result.status == ToolStatus.SUCCESS:
            cache_key = self.get_cache_key(input_data)
            cache.set(cache_key, result.to_dict(), self.config.cache_ttl_seconds)
    
    def record_usage(self, request, result: ToolResult) -> None:
        """Record tool usage for analytics"""
        try:
            self.analytics.track_tool_usage(
                tool_slug=self.config.slug,
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key,
                status=result.status.value,
                processing_time=result.processing_time_ms
            )
        except Exception as e:
            logger.warning(f"Failed to record usage for {self.config.slug}: {e}")
    
    def handle_error(self, error: Exception, context: str = "") -> ToolResult:
        """Standardized error handling"""
        error_msg = f"Error in {self.config.name}"
        if context:
            error_msg += f" ({context})"
        
        logger.error(f"{error_msg}: {str(error)}\n{traceback.format_exc()}")
        
        return ToolResult(
            status=ToolStatus.ERROR,
            error_message=f"{error_msg}: {str(error)}",
            metadata={'traceback': traceback.format_exc()}
        )
    
    def execute(self, request, input_data: Dict[str, Any]) -> ToolResult:
        """
        Main execution pipeline with validation, rate limiting, caching, and error handling.
        """
        import time
        start_time = time.time()
        
        try:
            # Rate limiting check
            if not self.rate_limiter.is_allowed(request):
                return ToolResult(
                    status=ToolStatus.RATE_LIMITED,
                    error_message="Rate limit exceeded. Please try again later."
                )
            
            # Input validation
            validation_errors = self.validate_input(input_data)
            if validation_errors:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    validation_errors=validation_errors,
                    error_message="Input validation failed"
                )
            
            # Check cache
            cached_result = self.get_cached_result(input_data)
            if cached_result:
                return cached_result
            
            # Execute main processing
            result = self.process(input_data)
            
            # Cache successful results
            self.cache_result(input_data, result)
            
            # Record usage
            result.processing_time_ms = int((time.time() - start_time) * 1000)
            self.record_usage(request, result)
            
            return result
            
        except Exception as e:
            return self.handle_error(e, "execute")
    
    def get_template_context(self, request) -> Dict[str, Any]:
        """Get template context for tool rendering"""
        return {
            'tool_config': self.config,
            'schema': self.get_schema(),
            'requires_auth': self.config.requires_auth,
            'seo_metadata': self.config.seo_metadata,
            'page_title': f"{self.config.name} — Free Online Tool | LamGen",
            'meta_description': self.config.description,
        }
    
    def render_tool_page(self, request) -> render:
        """Render tool page with standard template"""
        context = self.get_template_context(request)
        return render(request, f'tools/generic_tool.html', context)


class ToolRegistry:
    """
    Central registry for all tools in the ecosystem.
    Provides discovery, instantiation, and management of tools.
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, tool_class: type, config: ToolConfig) -> None:
        """Register a tool with the registry"""
        tool_instance = tool_class(config)
        self._tools[config.slug] = tool_instance
        
        # Add to category
        if config.category not in self._categories:
            self._categories[config.category] = []
        self._categories[config.category].append(config.slug)
    
    def get_tool(self, slug: str) -> Optional[BaseTool]:
        """Get tool instance by slug"""
        return self._tools.get(slug)
    
    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Get all tools in a category"""
        slugs = self._categories.get(category, [])
        return [self._tools[slug] for slug in slugs if slug in self._tools]
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools"""
        return self._tools.copy()
    
    def get_categories(self) -> Dict[str, List[str]]:
        """Get all categories and their tools"""
        return self._categories.copy()


# Global registry instance
tool_registry = ToolRegistry()


def register_tool(config: ToolConfig):
    """
    Decorator for registering tools with the global registry.
    
    Usage:
    @register_tool(ToolConfig(
        name="JSON Formatter",
        slug="json-formatter",
        category="developer",
        description="Format and validate JSON data"
    ))
    class JSONFormatterTool(BaseTool):
        ...
    """
    def decorator(tool_class):
        tool_registry.register(tool_class, config)
        return tool_class
    return decorator


def tool_view(tool_slug: str):
    """
    Decorator for creating standard tool views.
    Handles GET (render page) and POST (execute tool) requests.
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            tool = tool_registry.get_tool(tool_slug)
            if not tool:
                return JsonResponse({'error': 'Tool not found'}, status=404)
            
            if request.method == 'GET':
                return tool.render_tool_page(request)
            elif request.method == 'POST':
                try:
                    input_data = json.loads(request.body)
                    result = tool.execute(request, input_data)
                    return result.to_json_response()
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Invalid JSON'}, status=400)
            else:
                return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        return wrapped_view
    return decorator
