"""
Base Tool API Framework

Provides common functionality for all Developer Tools APIs including:
- Request validation and sanitization
- Rate limiting and security
- Error handling and logging
- Response formatting
- Analytics tracking
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Union
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from tools.models import Tool, ToolUsageHistory

logger = logging.getLogger('tools.api')


class APIResponse:
    """Standard API response format"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", metadata: Dict = None) -> JsonResponse:
        """Return successful response"""
        response = {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': timezone.now().isoformat(),
        }
        if metadata:
            response['metadata'] = metadata
        return JsonResponse(response, status=200)
    
    @staticmethod
    def error(message: str, code: str = "ERROR", details: Dict = None, status: int = 400) -> JsonResponse:
        """Return error response"""
        response = {
            'success': False,
            'message': message,
            'code': code,
            'timestamp': timezone.now().isoformat(),
        }
        if details:
            response['details'] = details
        return JsonResponse(response, status=status)


class BaseToolAPI:
    """Base class for all tool APIs"""
    
    def __init__(self, tool_slug: str):
        self.tool_slug = tool_slug
        self.tool = None
        self.rate_limit_key = f"tool_api_{tool_slug}"
        self.max_requests_per_minute = 60
        self.max_input_size = 10 * 1024 * 1024  # 10MB
        
    def get_tool(self) -> Tool:
        """Get tool object from database"""
        if not self.tool:
            try:
                self.tool = Tool.objects.get(slug=self.tool_slug, is_active=True)
            except Tool.DoesNotExist:
                raise ToolAPIError(f"Tool '{self.tool_slug}' not found", "TOOL_NOT_FOUND", 404)
        return self.tool
    
    def check_rate_limit(self, request: HttpRequest) -> None:
        """Check if user has exceeded rate limit"""
        # Use IP address or user ID for rate limiting
        identifier = request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR')
        key = f"{self.rate_limit_key}_{identifier}"
        
        # Get current requests from cache
        requests = cache.get(key, [])
        now = time.time()
        
        # Remove old requests (older than 1 minute)
        requests = [req_time for req_time in requests if now - req_time < 60]
        
        # Check if limit exceeded
        if len(requests) >= self.max_requests_per_minute:
            raise ToolAPIError(
                f"Rate limit exceeded. Maximum {self.max_requests_per_minute} requests per minute.",
                "RATE_LIMIT_EXCEEDED",
                429
            )
        
        # Add current request
        requests.append(now)
        cache.set(key, requests, 60)
    
    def validate_input_size(self, data: str) -> None:
        """Validate input size doesn't exceed limits"""
        if len(data.encode('utf-8')) > self.max_input_size:
            raise ToolAPIError(
                f"Input too large. Maximum size is {self.max_input_size // (1024*1024)}MB.",
                "INPUT_TOO_LARGE",
                413
            )
    
    def sanitize_input(self, data: str) -> str:
        """Sanitize input data"""
        if not isinstance(data, str):
            raise ValidationError("Input must be a string")
        
        # Remove potentially dangerous content
        # For most tools, we just ensure it's valid UTF-8
        try:
            data.encode('utf-8')
        except UnicodeEncodeError:
            raise ValidationError("Invalid character encoding")
        
        return data.strip()
    
    def track_usage(self, request: HttpRequest) -> None:
        """Track tool usage for analytics"""
        try:
            tool = self.get_tool()
            
            # Track in database for authenticated users
            if request.user.is_authenticated:
                ToolUsageHistory.objects.update_or_create(
                    user=request.user,
                    tool=tool,
                    defaults={}
                )
            
            # Increment usage count
            from django.db.models import F
            Tool.objects.filter(pk=tool.pk).update(usage_count=F('usage_count') + 1)
            
        except Exception as e:
            logger.error(f"Failed to track usage: {e}")
    
    def process_request(self, request: HttpRequest, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the tool request - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement process_request")
    
    @csrf_exempt
    @require_POST
    def handle_request(self, request: HttpRequest) -> JsonResponse:
        """Main request handler"""
        start_time = time.time()
        
        try:
            # Parse JSON input
            try:
                input_data = json.loads(request.body)
            except json.JSONDecodeError:
                return APIResponse.error("Invalid JSON input", "INVALID_JSON")
            
            # Check rate limiting
            self.check_rate_limit(request)
            
            # Validate and sanitize input
            if 'data' not in input_data:
                return APIResponse.error("Missing 'data' field", "MISSING_DATA")
            
            sanitized_data = self.sanitize_input(input_data['data'])
            self.validate_input_size(sanitized_data)
            
            # Process the request
            result = self.process_request(request, {
                'data': sanitized_data,
                'options': input_data.get('options', {})
            })
            
            # Track usage
            self.track_usage(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Return success response
            return APIResponse.success(
                data=result,
                message="Operation completed successfully",
                metadata={
                    'processing_time': round(processing_time, 3),
                    'tool': self.tool_slug,
                    'input_size': len(sanitized_data)
                }
            )
            
        except ToolAPIError as e:
            logger.warning(f"Tool API error: {e}")
            return APIResponse.error(e.message, e.code, e.details, e.status)
        
        except Exception as e:
            logger.error(f"Unexpected error in {self.tool_slug}: {e}", exc_info=True)
            return APIResponse.error(
                "Internal server error",
                "INTERNAL_ERROR",
                status=500
            )


class ToolAPIError(Exception):
    """Custom exception for tool API errors"""
    
    def __init__(self, message: str, code: str = "ERROR", status: int = 400, details: Dict = None):
        self.message = message
        self.code = code
        self.status = status
        self.details = details or {}
        super().__init__(message)


class ValidationError(ToolAPIError):
    """Validation error"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, "VALIDATION_ERROR", 400, details)


class ProcessingError(ToolAPIError):
    """Processing error"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, "PROCESSING_ERROR", 422, details)
