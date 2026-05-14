"""
API Middleware for Developer Tools

Provides rate limiting, security, and validation middleware for tool APIs.
"""

import time
import logging
from typing import Callable, Optional
from django.http import HttpRequest, JsonResponse
from django.core.cache import cache
from django.conf import settings
from .exceptions import RateLimitError, SecurityError
from .base import APIResponse

logger = logging.getLogger('tools.api')


def rate_limit(max_requests: int = 60, window_seconds: int = 60, 
                key_func: Optional[Callable] = None):
    """
    Rate limiting decorator for API endpoints
    
    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        key_func: Function to generate unique key for rate limiting
    """
    def decorator(view_func):
        def wrapper(request: HttpRequest, *args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func(request)
            else:
                # Default: use IP address or user ID
                key = f"rate_limit_{request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR')}"
            
            # Get current requests from cache
            requests = cache.get(key, [])
            now = time.time()
            
            # Remove old requests outside the window
            requests = [req_time for req_time in requests if now - req_time < window_seconds]
            
            # Check if limit exceeded
            if len(requests) >= max_requests:
                retry_after = int(window_seconds - (now - requests[0]))
                raise RateLimitError(
                    f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds.",
                    retry_after=retry_after
                )
            
            # Add current request
            requests.append(now)
            cache.set(key, requests, window_seconds)
            
            # Add rate limit headers
            response = view_func(request, *args, **kwargs)
            if isinstance(response, JsonResponse):
                response['X-RateLimit-Limit'] = str(max_requests)
                response['X-RateLimit-Remaining'] = str(max_requests - len(requests))
                response['X-RateLimit-Reset'] = str(int(now + window_seconds))
            
            return response
        
        return wrapper
    return decorator


def validate_input(max_size: int = 10 * 1024 * 1024, 
                   allowed_types: list = None,
                   sanitize: bool = True):
    """
    Input validation middleware
    
    Args:
        max_size: Maximum input size in bytes
        allowed_types: List of allowed content types
        sanitize: Whether to sanitize input
    """
    def decorator(view_func):
        def wrapper(request: HttpRequest, *args, **kwargs):
            # Check content size
            content_length = request.META.get('CONTENT_LENGTH')
            if content_length and int(content_length) > max_size:
                from .exceptions import FileSizeError
                raise FileSizeError(
                    f"Content too large. Maximum size is {max_size // (1024*1024)}MB.",
                    max_size=max_size,
                    actual_size=int(content_length)
                )
            
            # Check content type
            if allowed_types:
                content_type = request.META.get('CONTENT_TYPE', '').split(';')[0]
                if content_type not in allowed_types:
                    from .exceptions import UnsupportedFormatError
                    raise UnsupportedFormatError(
                        f"Content type {content_type} not allowed.",
                        format_type=content_type,
                        supported_formats=allowed_types
                    )
            
            # Basic security checks
            if sanitize:
                _security_scan(request)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def _security_scan(request: HttpRequest) -> None:
    """Perform basic security scan on request"""
    # Check for common attack patterns
    suspicious_patterns = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers
        r'union.*select',  # SQL injection (basic)
        r'eval\s*\(',  # eval function
        r'document\.',  # Document object access
    ]
    
    import re
    
    # Scan request body
    if hasattr(request, 'body'):
        body = request.body.decode('utf-8', errors='ignore').lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                logger.warning(f"Suspicious pattern detected: {pattern}")
                raise SecurityError(
                    "Request contains potentially malicious content",
                    security_issue=f"Pattern: {pattern}"
                )
    
    # Scan query parameters
    for param, value in request.GET.items():
        value_str = str(value).lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, value_str, re.IGNORECASE):
                logger.warning(f"Suspicious pattern in parameter {param}: {pattern}")
                raise SecurityError(
                    "Request contains potentially malicious content",
                    security_issue=f"Parameter: {param}, Pattern: {pattern}"
                )


def cors(allow_origins: list = None, allow_methods: list = None, 
         allow_headers: list = None, max_age: int = 86400):
    """
    CORS middleware for API endpoints
    
    Args:
        allow_origins: List of allowed origins
        allow_methods: List of allowed HTTP methods
        allow_headers: List of allowed headers
        max_age: Cache time for preflight requests
    """
    def decorator(view_func):
        def wrapper(request: HttpRequest, *args, **kwargs):
            # Handle preflight request
            if request.method == 'OPTIONS':
                response = JsonResponse({'status': 'ok'})
            else:
                response = view_func(request, *args, **kwargs)
            
            # Add CORS headers
            if allow_origins:
                origin = request.META.get('HTTP_ORIGIN')
                if origin in allow_origins or '*' in allow_origins:
                    response['Access-Control-Allow-Origin'] = origin if origin in allow_origins else '*'
            
            if allow_methods:
                response['Access-Control-Allow-Methods'] = ', '.join(allow_methods)
            
            if allow_headers:
                response['Access-Control-Allow-Headers'] = ', '.join(allow_headers)
            
            response['Access-Control-Max-Age'] = str(max_age)
            
            return response
        
        return wrapper
    return decorator


def require_auth(view_func):
    """Require authentication for API endpoint"""
    def wrapper(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return APIResponse.error(
                "Authentication required",
                "AUTH_REQUIRED",
                status=401
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def api_key_required(api_key_param: str = 'api_key'):
    """Require valid API key for endpoint"""
    def decorator(view_func):
        def wrapper(request: HttpRequest, *args, **kwargs):
            api_key = request.GET.get(api_key_param) or request.META.get(f'HTTP_{api_key_param.upper()}')
            
            if not api_key:
                return APIResponse.error(
                    "API key required",
                    "API_KEY_REQUIRED",
                    status=401
                )
            
            # Validate API key (implement your own logic)
            if not _validate_api_key(api_key):
                return APIResponse.error(
                    "Invalid API key",
                    "INVALID_API_KEY",
                    status=401
                )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def _validate_api_key(api_key: str) -> bool:
    """Validate API key - implement your own logic"""
    # This is a placeholder - implement proper API key validation
    valid_keys = getattr(settings, 'VALID_API_KEYS', [])
    return api_key in valid_keys


def logging_middleware(view_func):
    """Log API requests and responses"""
    def wrapper(request: HttpRequest, *args, **kwargs):
        start_time = time.time()
        
        # Log request
        logger.info(f"API Request: {request.method} {request.path} from {request.META.get('REMOTE_ADDR')}")
        
        try:
            response = view_func(request, *args, **kwargs)
            
            # Log response
            duration = time.time() - start_time
            status_code = getattr(response, 'status_code', 200)
            logger.info(f"API Response: {status_code} in {duration:.3f}s")
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(f"API Error: {str(e)} in {duration:.3f}s")
            raise
    
    return wrapper


def cache_response(timeout: int = 300, key_func: Optional[Callable] = None):
    """Cache API responses"""
    def decorator(view_func):
        def wrapper(request: HttpRequest, *args, **kwargs):
            # Generate cache key
            if key_func:
                key = key_func(request)
            else:
                # Default: use path and method
                key = f"api_cache_{request.method}_{request.path}"
            
            # Try to get from cache
            cached_response = cache.get(key)
            if cached_response:
                return cached_response
            
            # Execute and cache response
            response = view_func(request, *args, **kwargs)
            if isinstance(response, JsonResponse):
                cache.set(key, response, timeout)
            
            return response
        
        return wrapper
    return decorator


# Common middleware combinations
def standard_api_middleware(view_func):
    """Standard middleware stack for most API endpoints"""
    return logging_middleware(
        rate_limit(max_requests=60, window_seconds=60)(
            validate_input(max_size=10*1024*1024)(
                cors(allow_origins=['*'], allow_methods=['POST', 'OPTIONS'])(
                    view_func
                )
            )
        )
    )


def premium_api_middleware(view_func):
    """Premium middleware stack for authenticated endpoints"""
    return logging_middleware(
        require_auth(
            rate_limit(max_requests=120, window_seconds=60)(
                validate_input(max_size=50*1024*1024)(
                    cors(allow_origins=['*'], allow_methods=['POST', 'OPTIONS'])(
                        view_func
                    )
                )
            )
        )
    )
