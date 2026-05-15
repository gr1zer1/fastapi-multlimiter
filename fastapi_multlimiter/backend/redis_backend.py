from .base import BaseBackend
import redis.asyncio as redis
from datetime import datetime,timezone,timedelta
import json


TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local refill_rate = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if tokens == nil then
    tokens = capacity - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, math.ceil(capacity / refill_rate))
    return {1, tokens, 0}
end

local new_tokens = math.min(capacity, tokens + (now - last_refill) * refill_rate)

if new_tokens < 1 then
    return {0, new_tokens, 1 / refill_rate}
end

new_tokens = new_tokens - 1
redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
return {1, new_tokens, 0}
"""


class RedisBackend(BaseBackend):
    """Redis backend for distributed rate limiting.

    Stores fixed-window counters as string keys and sliding-window timestamps
    as sorted sets.
    """

    expire: int | None = None

    def __init__(self,url: str):
        """Create a Redis backend.

        Args:
            url: Redis connection URL, for example ``redis://localhost:6379``.
        """
        self.expire: int | None = None
        self.client: redis.Redis = redis.from_url(url, decode_responses=True)


    async def get(self, key: str) -> dict | None:
        """Return fixed-window counter payload for ``key`` if it exists."""
        redis_key = f"fw:{key}"

        value = await self.client.get(redis_key)

        if value is None:
            return None

        ttl = await self.client.ttl(redis_key)

        return {
            "counter": int(value),
            "ttl": ttl,
        }

    async def put(self, key: str) -> dict:
        """Create a fixed-window counter if needed and increment it."""
        redis_key = f"fw:{key}"

        await self.client.set(redis_key, 0, ex=self.expire, nx=True)
        return await self.increment(key)

    async def increment(self, key: str) -> dict:
        """Increment fixed-window counter for ``key`` and return its TTL."""
        redis_key = f"fw:{key}"

        value = await self.client.incr(redis_key)

        if value == 1:
            await self.client.expire(
                redis_key,
                self.expire,
            )

        ttl = await self.client.ttl(redis_key)

        return {
            "counter": value,
            "ttl": ttl,
        }


    async def append(self, key: str, timestamp: float):
        """Add a timestamp to the sliding-window sorted set for ``key``."""
        await self.client.zadd(
            f"sw:{key}",
            {str(timestamp): timestamp}
        )

    async def get_range(self, key: str, from_time: float) -> list[float]:
        """Return sliding-window timestamps newer than ``from_time``.

        Older timestamps are removed before reading the range.
        """
        await self.client.zremrangebyscore(
            f"sw:{key}",
            "-inf",
            from_time-1
        )
        return await self.client.zrangebyscore(
            f"sw:{key}",
            from_time,
            "+inf"
        )


    async def consume_token(self,
                            key: str,
                            capacity: int,
                            refill_rate: float,
                            now: float
                        ) -> dict:
        """Consume one token from a Redis-backed token bucket.

        The operation is executed with a Lua script so refill and consumption
        happen atomically for a single key.

        Returns:
            A dictionary containing:
            ``check``: whether the request is allowed,
            ``remain``: remaining tokens in the bucket,
            ``after``: seconds until another token is available.
        """
        res = await self.client.eval(TOKEN_BUCKET_SCRIPT, 1, key , now, capacity, refill_rate)
        print("EVAL RESULT:", res)
        return {
            "check": bool(res[0]),
            "remain": float(res[1]),
            "after": float(res[2])
        }


    async def get_time_fw(self, key: str) -> float:
        """Return Redis TTL for the fixed-window counter."""
        redis_key = f"fw:{key}"

        ttl = await self.client.ttl(redis_key)
        return ttl
    
    async def get_time_sw(self, key):
        """Return seconds until the oldest request leaves the sliding window."""

        time = datetime.now(timezone.utc) - timedelta(seconds=self.expire)
        
        res_range = await self.get_range(key,time.timestamp())
        timestamp = float(res_range[0])

        return (timestamp + self.expire) - datetime.now(timezone.utc).timestamp()
    
    
    async def _clear(self):
        """Flush all Redis data.

        This method is intended for tests. Do not use it against shared Redis
        databases.
        """
        await self.client.flushall()

    async def close(self):
        """Close Redis client connections."""
        await self.client.close()
        await self.client.connection_pool.disconnect()
