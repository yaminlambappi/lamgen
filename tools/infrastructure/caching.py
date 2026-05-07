"""
Caching Infrastructure - Complete Implementation of Caching System

Provides production-ready caching with Redis, memory cache, cache warming,
and cache management for the LamGen tools ecosystem.
"""

import json
import time
import hashlib
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

# Try to import Redis, but make it optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class CacheBackend(Enum):
    """Cache backend types"""
    MEMORY = "memory"
    REDIS = "redis"
    HYBRID = "hybrid"


@dataclass
class CacheConfig:
    """Cache configuration"""
    backend: CacheBackend = CacheBackend.MEMORY
    default_ttl: int = 3600  # 1 hour
    max_size: int = 1000
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    key_prefix: str = "lamgen:"
    compression: bool = False


@dataclass
class CacheEntry:
    """Cache entry data"""
    key: str
    value: Any
    ttl: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class CacheBackendBase(ABC):
    """Abstract cache backend"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        pass


class MemoryCache(CacheBackendBase):
    """In-memory cache backend"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = config.max_size
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        entry = self.cache.get(key)
        
        if not entry:
            return None
        
        # Check expiration
        if entry.expires_at and datetime.now() > entry.expires_at:
            del self.cache[key]
            return None
        
        # Update access info
        entry.access_count += 1
        entry.last_accessed = datetime.now()
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache"""
        # Check size limit
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()
        
        # Calculate expiration
        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)
        elif self.config.default_ttl:
            expires_at = datetime.now() + timedelta(seconds=self.config.default_ttl)
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            ttl=ttl,
            expires_at=expires_at
        )
        
        self.cache[key] = entry
        return True
    
    def delete(self, key: str) -> bool:
        """Delete value from memory cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        self.cache.clear()
        return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        entry = self.cache.get(key)
        if not entry:
            return False
        
        # Check expiration
        if entry.expires_at and datetime.now() > entry.expires_at:
            del self.cache[key]
            return False
        
        return True
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        import fnmatch
        return [key for key in self.cache.keys() if fnmatch.fnmatch(key, pattern)]
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self.cache.keys(),
            key=lambda k: (
                self.cache[k].last_accessed or datetime.min,
                self.cache[k].access_count
            )
        )
        
        del self.cache[lru_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        expired_entries = 0
        
        for entry in self.cache.values():
            if entry.expires_at and datetime.now() > entry.expires_at:
                expired_entries += 1
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'max_size': self.max_size,
            'utilization': (total_entries / self.max_size) * 100 if self.max_size > 0 else 0,
            'backend': 'memory'
        }


class RedisCache(CacheBackendBase):
    """Redis cache backend"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        if not REDIS_AVAILABLE:
            raise ImportError("Redis is not available. Install with: pip install redis")
        
        # Initialize Redis client
        self.redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            password=config.redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # Test connection
        try:
            self.redis_client.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        try:
            full_key = self.config.key_prefix + key
            value = self.redis_client.get(full_key)
            
            if value is None:
                return None
            
            # Deserialize value
            return self._deserialize(value)
            
        except Exception as e:
            self.logger.error(f"Error getting from Redis: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache"""
        try:
            full_key = self.config.key_prefix + key
            serialized_value = self._serialize(value)
            
            # Use provided TTL or default
            expire_time = ttl or self.config.default_ttl
            
            self.redis_client.setex(full_key, expire_time, serialized_value)
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting to Redis: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from Redis cache"""
        try:
            full_key = self.config.key_prefix + key
            result = self.redis_client.delete(full_key)
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting from Redis: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            pattern = self.config.key_prefix + "*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing Redis: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache"""
        try:
            full_key = self.config.key_prefix + key
            return bool(self.redis_client.exists(full_key))
            
        except Exception as e:
            self.logger.error(f"Error checking existence in Redis: {str(e)}")
            return False
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        try:
            full_pattern = self.config.key_prefix + pattern
            redis_keys = self.redis_client.keys(full_pattern)
            
            # Remove key prefix
            return [key[len(self.config.key_prefix):] for key in redis_keys]
            
        except Exception as e:
            self.logger.error(f"Error getting keys from Redis: {str(e)}")
            return []
    
    def _serialize(self, value: Any) -> str:
        """Serialize value for Redis storage"""
        try:
            if self.config.compression:
                # Would implement compression here
                pass
            
            return json.dumps(value, default=str)
            
        except Exception as e:
            self.logger.error(f"Error serializing value: {str(e)}")
            raise
    
    def _deserialize(self, value: str) -> Any:
        """Deserialize value from Redis storage"""
        try:
            return json.loads(value)
            
        except Exception as e:
            self.logger.error(f"Error deserializing value: {str(e)}")
            return value
    
    def get_redis_info(self) -> Dict[str, Any]:
        """Get Redis server info"""
        try:
            info = self.redis_client.info()
            return {
                'used_memory': info.get('used_memory', 0),
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'backend': 'redis'
            }
        except Exception as e:
            self.logger.error(f"Error getting Redis info: {str(e)}")
            return {}


class HybridCache(CacheBackendBase):
    """Hybrid cache backend (L1: Memory, L2: Redis)"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.memory_cache = MemoryCache(config)
        self.redis_cache = RedisCache(config) if REDIS_AVAILABLE else None
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from hybrid cache"""
        # Try L1 (memory) first
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Try L2 (Redis)
        if self.redis_cache:
            value = self.redis_cache.get(key)
            if value is not None:
                # Store in L1 for faster access
                self.memory_cache.set(key, value)
                return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in hybrid cache"""
        # Set in both L1 and L2
        memory_success = self.memory_cache.set(key, value, ttl)
        
        redis_success = True
        if self.redis_cache:
            redis_success = self.redis_cache.set(key, value, ttl)
        
        return memory_success and redis_success
    
    def delete(self, key: str) -> bool:
        """Delete value from hybrid cache"""
        memory_success = self.memory_cache.delete(key)
        
        redis_success = True
        if self.redis_cache:
            redis_success = self.redis_cache.delete(key)
        
        return memory_success or redis_success
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        memory_success = self.memory_cache.clear()
        
        redis_success = True
        if self.redis_cache:
            redis_success = self.redis_cache.clear()
        
        return memory_success and redis_success
    
    def exists(self, key: str) -> bool:
        """Check if key exists in hybrid cache"""
        return self.memory_cache.exists(key) or (
            self.redis_cache and self.redis_cache.exists(key)
        )
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        memory_keys = set(self.memory_cache.keys(pattern))
        
        redis_keys = set()
        if self.redis_cache:
            redis_keys = set(self.redis_cache.keys(pattern))
        
        return list(memory_keys.union(redis_keys))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get hybrid cache statistics"""
        stats = {
            'backend': 'hybrid',
            'memory_stats': self.memory_cache.get_stats()
        }
        
        if self.redis_cache:
            stats['redis_stats'] = self.redis_cache.get_redis_info()
        
        return stats


class CacheManager:
    """Production-ready cache manager"""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.backend = self._create_backend()
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    def _create_backend(self) -> CacheBackendBase:
        """Create cache backend based on configuration"""
        if self.config.backend == CacheBackend.MEMORY:
            return MemoryCache(self.config)
        elif self.config.backend == CacheBackend.REDIS:
            return RedisCache(self.config)
        elif self.config.backend == CacheBackend.HYBRID:
            return HybridCache(self.config)
        else:
            raise ValueError(f"Unsupported cache backend: {self.config.backend}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        value = self.backend.get(key)
        
        if value is None:
            self.stats['misses'] += 1
            return default
        else:
            self.stats['hits'] += 1
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        success = self.backend.set(key, value, ttl)
        if success:
            self.stats['sets'] += 1
        return success
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        success = self.backend.delete(key)
        if success:
            self.stats['deletes'] += 1
        return success
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        return self.backend.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        return self.backend.exists(key)
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        return self.backend.keys(pattern)
    
    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        """Get value from cache or set using factory function"""
        value = self.get(key)
        
        if value is None:
            value = factory()
            self.set(key, value, ttl)
        
        return value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = 0
        total_requests = self.stats['hits'] + self.stats['misses']
        if total_requests > 0:
            hit_rate = (self.stats['hits'] / total_requests) * 100
        
        stats = {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }
        
        # Add backend-specific stats
        if hasattr(self.backend, 'get_stats'):
            stats['backend_stats'] = self.backend.get_stats()
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset cache statistics"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }


class CacheWarmer:
    """Production-ready cache warmer"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
        self.warmup_tasks = []
    
    def add_warmup_task(self, key: str, factory: Callable[[], Any], ttl: Optional[int] = None) -> None:
        """Add a cache warmup task"""
        self.warmup_tasks.append({
            'key': key,
            'factory': factory,
            'ttl': ttl
        })
    
    def warm_cache(self) -> Dict[str, Any]:
        """Warm up cache with all registered tasks"""
        results = {
            'total_tasks': len(self.warmup_tasks),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        start_time = time.time()
        
        for task in self.warmup_tasks:
            try:
                value = task['factory']()
                success = self.cache_manager.set(task['key'], value, task['ttl'])
                
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to set cache key: {task['key']}")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error warming cache key {task['key']}: {str(e)}")
                self.logger.error(f"Cache warmup error for key {task['key']}: {str(e)}")
        
        results['duration'] = time.time() - start_time
        results['timestamp'] = datetime.now().isoformat()
        
        self.logger.info(f"Cache warmup completed: {results['successful']}/{results['total_tasks']} successful")
        
        return results
    
    def warm_key(self, key: str, factory: Callable[[], Any], ttl: Optional[int] = None) -> bool:
        """Warm up a specific cache key"""
        try:
            value = factory()
            return self.cache_manager.set(key, value, ttl)
        except Exception as e:
            self.logger.error(f"Error warming cache key {key}: {str(e)}")
            return False


# Global cache instance
_cache_manager = None


def get_cache_manager(config: CacheConfig = None) -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager(config)
    
    return _cache_manager


def cache_result(ttl: int = None, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Generate cache key
            cache_key = f"{key_prefix}{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            
            if result is None:
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Cache key utilities
def make_cache_key(*parts: str) -> str:
    """Create cache key from parts"""
    return ":".join(str(part) for part in parts)


def hash_cache_key(key: str) -> str:
    """Create hash of cache key for long keys"""
    return hashlib.md5(key.encode()).hexdigest()
