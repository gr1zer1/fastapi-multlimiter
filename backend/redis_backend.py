from .base import BaseBackend
import redis.asyncio as redis
from datetime import datetime,timezone,timedelta
import json


class RedisBackend(BaseBackend):

    expire: int | None = None

    def __init__(self,url: str):
        self.expire: int | None = None
        self.client: redis.Redis = redis.from_url(url, decode_responses=True)

 
    async def get(self, key: str) -> dict | None:
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
        redis_key = f"fw:{key}"

        await self.client.set(redis_key, 0, ex=self.expire, nx=True)
        return await self.increment(key)

    async def increment(self, key: str) -> dict:
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
        await self.client.zadd(
            f"sw:{key}",
            {str(timestamp): timestamp}
        )

    async def get_range(self, key: str, from_time: float) -> list[float]:
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

    async def get_time_fw(self, key: str) -> float:
        redis_key = f"fw:{key}"

        ttl = await self.client.ttl(redis_key)
        return ttl
    
    async def get_time_sw(self, key):

        time = datetime.now(timezone.utc) - timedelta(seconds=self.expire)
        
        res_range = await self.get_range(key,time.timestamp())
        timestamp = float(res_range[0])

        return (timestamp + self.expire) - datetime.now(timezone.utc).timestamp()
      

    async def _clear(self):
        await self.client.flushall()

    async def close(self):
        await self.client.close()
        await self.client.connection_pool.disconnect()