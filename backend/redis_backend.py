from .base import BaseBackend
import redis.asyncio as redis
from datetime import datetime,timezone,timedelta
import json


class RedisBackend(BaseBackend):

    expire: int | None = None

    def __init__(self,url: str):
        self.expire: int | None = None
        self.client: redis.Redis = redis.from_url(url)

 
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

        response = await self.get(key)

        if response is not None:
            return await self.increment(key)

        await self.client.set(
            redis_key,
            1,
            ex=self.expire,
        )

        return {
            "counter": 1,
            "ttl": self.expire,
        }

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

    async def append(self, key, timestamp):
        pass

    async def get_range(self, key, from_time):
        pass

    async def _clear(self):
        pass