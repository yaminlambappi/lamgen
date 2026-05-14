"""
Enhanced Rate Limiting Framework - Production-Ready Rate Limiting for LamGen Tools

Implements sophisticated rate limiting with Redis backend,
supporting multiple strategies and granular control.
"""

import time
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.conf import settings
from django.utils import timezone


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10  # For token bucket
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW


class RateLimitResult:
    """Result of rate limit check"""
    def __init__(self, allowed: bool, remaining: int, reset_time: int):
        self.allowed = allowed
        self.remaining = remaining
        self.reset_time = reset_time  # Unix timestamp
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'allowed': self.allowed,
            'remaining': self.remaining,
            'reset_time': self.reset_time
        }


class RateLimiter:
    """
    Production-ready rate limiter with Redis backend.
    Supports multiple strategies and provides detailed feedback.
    """
    
    def __init__(self, requests_per_minute: int = 60, strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW):
        self.config = RateLimitConfig(requests_per_minute=requests_per_minute, strategy=strategy)
        
    def is_allowed(self, request: HttpRequest) -> bool:
        """Check if request is allowed"""
        result = self.check_rate_limit(request)
        return result.allowed
    
    def check_rate_limit(self, request: HttpRequest) -> RateLimitResult:
        """Detailed rate limit check with remaining count and reset time"""
        key = self._get_key(request)
        
        if self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._sliding_window_check(key)
        elif self.config.strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._fixed_window_check(key)
        elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._token_bucket_check(key)
        else:
            # Fallback to sliding window
            return self._sliding_window_check(key)
    
    def _get_key(self, request: HttpRequest) -> str:
        """Generate rate limit key for request"""
        # Use IP address for anonymous users, user ID for authenticated users
        if request.user.is_authenticated:
            identifier = f"user:{request.user.id}"
        else:
            # Get IP address from request
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR', 'unknown')
            identifier = f"ip:{ip}"
        
        # Add tool-specific key if available
        tool_slug = getattr(request, 'tool_slug', None)
        if tool_slug:
            identifier = f"{identifier}:tool:{tool_slug}"
        
        return f"rate_limit:{identifier}"
    
    def _sliding_window_check(self, key: str) -> RateLimitResult:
        """Sliding window rate limiting"""
        now = time.time()
        window_start = now - 60  # 1 minute window
        
        # Get existing requests in window
        existing_data = cache.get(key, '[]')
        try:
            requests = json.loads(existing_data)
        except (json.JSONDecodeError, TypeError):
            requests = []
        
        # Filter out old requests outside window
        requests = [req_time for req_time in requests if req_time > window_start]
        
        # Check if adding current request exceeds limit
        if len(requests) >= self.config.requests_per_minute:
            # Find when the oldest request expires
            if requests:
                reset_time = int(requests[0] + 60)
            else:
                reset_time = int(now + 60)
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time
            )
        
        # Add current request
        requests.append(now)
        
        # Update cache with new requests list
        cache.set(key, json.dumps(requests), 3600)  # Keep for 1 hour
        
        return RateLimitResult(
            allowed=True,
            remaining=self.config.requests_per_minute - len(requests),
            reset_time=int(now + 60)
        )
    
    def _fixed_window_check(self, key: str) -> RateLimitResult:
        """Fixed window rate limiting"""
        now = int(time.time())
        current_minute = now // 60
        window_key = f"{key}:{current_minute}"
        
        # Get current count for this minute
        current_count = cache.get(window_key, 0)
        
        if current_count >= self.config.requests_per_minute:
            # Reset at next minute
            reset_time = (current_minute + 1) * 60
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time
            )
        
        # Increment count
        new_count = current_count + 1
        cache.set(window_key, new_count, 120)  # Keep for 2 minutes
        
        return RateLimitResult(
            allowed=True,
            remaining=self.config.requests_per_minute - new_count,
            reset_time=(current_minute + 1) * 60
        )
    
    def _token_bucket_check(self, key: str) -> RateLimitResult:
        """Token bucket rate limiting"""
        now = time.time()
        
        # Get current bucket state
        bucket_data = cache.get(key, '{"tokens": 0, "last_refill": 0}')
        try:
            bucket = json.loads(bucket_data)
        except (json.JSONDecodeError, TypeError):
            bucket = {"tokens": 0, "last_refill": 0}
        
        # Refill tokens based on time elapsed
        time_elapsed = now - bucket["last_refill"]
        tokens_to_add = time_elapsed * (self.config.requests_per_minute / 60)
        
        # Refill bucket, but don't exceed burst size
        bucket["tokens"] = min(
            bucket["tokens"] + tokens_to_add,
            self.config.burst_size
        )
        bucket["last_refill"] = now
        
        if bucket["tokens"] < 1:
            # Calculate when next token will be available
            tokens_needed = 1 - bucket["tokens"]
            time_to_wait = tokens_needed * (60 / self.config.requests_per_minute)
            reset_time = int(now + time_to_wait)
            
            # Update bucket state
            cache.set(key, json.dumps(bucket), 3600)
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time
            )
        
        # Consume one token
        bucket["tokens"] -= 1
        
        # Update bucket state
        cache.set(key, json.dumps(bucket), 3600)
        
        return RateLimitResult(
            allowed=True,
            remaining=int(bucket["tokens"]),
            reset_time=int(now + 60)
        )
    
    def get_headers(self, result: RateLimitResult) -> Dict[str, str]:
        """Generate rate limit headers for HTTP response"""
        return {
            'X-RateLimit-Limit': str(self.config.requests_per_minute),
            'X-RateLimit-Remaining': str(result.remaining),
            'X-RateLimit-Reset': str(result.reset_time),
            'Retry-After': str(result.reset_time) if not result.allowed else ''
        }


# Legacy decorator for backward compatibility
def rate_limit(key_prefix: str, limit: int = 60, window: int = 60):
    """
    Decorator factory for cache-based rate limiting.

    Usage:
        @rate_limit('search', limit=60, window=60)
        def my_view(request): ...
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
            ip = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR', 'unknown')
            cache_key = f'rl:{key_prefix}:{ip}'
            count = cache.get(cache_key, 0)
            if count >= limit:
                return JsonResponse({'error': 'Rate limit exceeded. Please slow down.'}, status=429)
            cache.set(cache_key, count + 1, window)
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        wrapper.__doc__ = view_func.__doc__
        return wrapper
    return decorator
