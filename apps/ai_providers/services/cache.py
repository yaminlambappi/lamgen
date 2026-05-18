from functools import wraps
import hashlib
import json
from django.core.cache import cache

def cache_generation(ttl=60 * 60):
    def decorator(func):
        @wraps(func)
        def wrapper(self, prompt, **kwargs):
            key_dict = {"prompt": prompt, **kwargs}
            key = hashlib.md5(json.dumps(key_dict, sort_keys=True).encode()).hexdigest()

            cached_result = cache.get(key)
            if cached_result:
                return cached_result

            result = func(self, prompt, **kwargs)
            cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator

def cache_generation_async(ttl=60 * 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, prompt, **kwargs):
            key_dict = {"prompt": prompt, **kwargs}
            key = hashlib.md5(json.dumps(key_dict, sort_keys=True).encode()).hexdigest()

            cached_result = cache.get(key)
            if cached_result:
                return cached_result

            result = await func(self, prompt, **kwargs)
            cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator
