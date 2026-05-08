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
        response =  self.client.get(f"fw:{key}")
        if response is not None:
            # decoded_response = json.loads(response)
            return {"counter":response}
        else:
            return None
        


    async def put(self, key: str) -> dict:
        if await self.get(key) is not None:

            return await self.increment(key)

        # payload = {"counter":1,"expire_at":datetime.now(timezone.utc) + timedelta(seconds=self.expire)}
        # value = json.dumps(payload)
        
        self.client.set(f"fw:{key}", 1, self.expire)
        return {"counter":1}


    async def increment(self, key: str) -> int | dict:
        res = await self.get(key)
        
        if res is not None:
            
            self.client.set(f"fw:{key}", res+1, keepttl=True)
        else:
            return await self.put(key)

