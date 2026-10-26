import json

import redis.asyncio as redis

from app.core.config import settings

_redis: redis.Redis | None = None


def connect():
    global _redis
    _redis = redis.from_url(settings.redis_url, decode_responses=True)


def close():
    global _redis
    _redis = None


def get_redis() -> redis.Redis:
    if _redis is None:
        connect()
    return _redis


async def cache_get(key: str):
    r = get_redis()
    raw = await r.get(key)
    return json.loads(raw) if raw else None


async def cache_set(key: str, value, ttl: int = None):
    r = get_redis()
    await r.set(key, json.dumps(value, default=str), ex=ttl or settings.cache_ttl_seconds)


async def cache_delete(*keys: str):
    r = get_redis()
    if keys:
        await r.delete(*keys)


async def rate_window_count(key: str, window_seconds: int) -> int:
    """Sliding counter used by fraud velocity checks: push a timestamp, trim the
    window, and return how many events fall inside it."""
    import time

    r = get_redis()
    now = time.time()
    pipe = r.pipeline()
    pipe.zadd(key, {str(now): now})
    pipe.zremrangebyscore(key, 0, now - window_seconds)
    pipe.zcard(key)
    pipe.expire(key, window_seconds + 5)
    _, _, count, _ = await pipe.execute()
    return count
