from django.core.cache import cache

class CacheManager:
    def get(self, key):
        return cache.get(key)

    def set(self, key, value, timeout=3600):
        cache.set(key, value, timeout)
