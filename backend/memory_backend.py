from .base import BaseBackend
from datetime import datetime,timezone,timedelta


class MemoryBackend(BaseBackend):


    def __init__(self, expire: int):
        self.counter: dict[str,dict] = dict()
        self.expire = expire


    async def put(self, key: str) -> dict:
        if self.counter.get(key) is not None:

            return await self.increment(key)

        payload = {"counter":1,"expire_at":datetime.now(timezone.utc) + timedelta(seconds=self.expire)}

        self.counter[key] = payload
        return payload
    

    async def get(self, key: str) -> dict | None:
        return self.counter.get(key)
    

    async def increment(self, key: str) -> int | dict:
        if self.counter.get(key) is not None:
            if datetime.now(timezone.utc) > self.counter[key]["expire_at"]:
                self.counter[key]["counter"] = 0
                payload = {"counter":0,"expire_at":datetime.now(timezone.utc) + timedelta(seconds=self.expire)}

                self.counter[key] = payload

            
            self.counter[key]["counter"] +=1
            return self.counter[key]
        else:
            return await self.put(key)
