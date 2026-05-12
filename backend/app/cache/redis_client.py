import json

from redis.asyncio import Redis, ConnectionError

from app.config import settings

redis: Redis | None = None


async def init_redis() -> None:
    global redis
    redis = Redis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    if redis is not None:
        await redis.aclose()


async def get_cached_wallet(address: str) -> dict | None:
    if redis is None:
        return None
    try:
        cached = await redis.get(f"wallet:{address}")
        return json.loads(cached) if cached else None
    except ConnectionError:
        return None


async def set_cached_wallet(address: str, data: dict) -> None:
    if redis is None:
        return
    try:
        await redis.set(f"wallet:{address}", json.dumps(data), ex=settings.bulk_cache_ttl_seconds)
    except ConnectionError:
        pass
