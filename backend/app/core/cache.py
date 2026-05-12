"""
缓存模块：支持 Redis 和内存缓存
"""
import json
import hashlib
import time
from typing import Optional, Any
from functools import wraps

from app.core.config import settings


class MemoryCache:
    """内存缓存实现"""

    def __init__(self, default_ttl: int = 3600):
        self._cache: dict = {}
        self._ttl: int = default_ttl

    def _make_key(self, key: str) -> str:
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        cache_key = self._make_key(key)
        item = self._cache.get(cache_key)
        if item is None:
            return None
        if time.time() > item["expires_at"]:
            del self._cache[cache_key]
            return None
        return json.loads(item["value"])

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        cache_key = self._make_key(key)
        self._cache[cache_key] = {
            "value": json.dumps(value, ensure_ascii=False, default=str),
            "expires_at": time.time() + (ttl or self._ttl),
        }
        return True

    def delete(self, key: str) -> bool:
        cache_key = self._make_key(key)
        if cache_key in self._cache:
            del self._cache[cache_key]
            return True
        return False

    def clear(self) -> bool:
        self._cache.clear()
        return True


class RedisCache:
    """Redis 缓存实现"""

    def __init__(self, default_ttl: int = 3600):
        import redis
        self._client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        self._ttl: int = default_ttl

    def get(self, key: str) -> Optional[Any]:
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
        except Exception:
            pass
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            self._client.setex(key, ttl or self._ttl, json.dumps(value, ensure_ascii=False, default=str))
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        try:
            self._client.delete(key)
            return True
        except Exception:
            return False

    def clear(self) -> bool:
        try:
            self._client.flushdb()
            return True
        except Exception:
            return False


class CacheManager:
    """缓存管理器"""

    _instance: Optional[Any] = None

    def __new__(cls):
        if cls._instance is None:
            if settings.redis_enabled:
                try:
                    cls._instance = RedisCache()
                except Exception:
                    cls._instance = MemoryCache()
            else:
                cls._instance = MemoryCache()
        return cls._instance


cache = CacheManager()


def cached(ttl: int = 3600, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return async_wrapper if func.__code__.co_flags & 0x80 else sync_wrapper
    return decorator
