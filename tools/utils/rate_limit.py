"""Cache-based rate limiting decorator for Django views."""
from django.core.cache import cache
from django.http import JsonResponse


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
