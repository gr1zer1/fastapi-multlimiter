from .base import BaseBackend
from datetime import datetime,timezone,timedelta


class MemoryBackend(BaseBackend):
    expire: int | None = None

    def __init__(self):
        self.counter: dict[str,dict | list] = dict()
        self.expire: float | None = None


    async def put(self, key: str) -> dict:
        if await self.get(key) is not None:

            return await self.increment(key)

        payload = {"counter":1,"expire_at":datetime.now(timezone.utc) + timedelta(seconds=self.expire)}

        self.counter[f"fw:{key}"] = payload
        return payload
    

    async def get(self, key: str) -> dict | None:
        return self.counter.get(f"fw:{key}")
    

    async def increment(self, key: str) -> int | dict:
        res = await self.get(key)
        
        if res is not None:
            if datetime.now(timezone.utc) > res["expire_at"]:
                res["counter"] = 0
                payload = {"counter":0,"expire_at":datetime.now(timezone.utc) + timedelta(seconds=self.expire)}

                self.counter[f"fw:{key}"] = payload

            
            self.counter[f"fw:{key}"]["counter"] +=1
            return self.counter[f"fw:{key}"]
        else:
            return await self.put(key)
    

    async def append(self, key: str, timestamp: float):
        res = self.counter.get(f"sw:{key}")

        if res is None:

            self.counter[f"sw:{key}"] = [timestamp]
        else:
            self.counter[f"sw:{key}"].append(timestamp)


    async def get_range(self, key: str, from_time: float) -> list[float]:
        res = self.counter.get(f"sw:{key}")
        if res is None:
            return [] 
        await self.cleanup(key)
        return  list(filter(lambda t: t>from_time,res))
    

    async def get_time_fw(self, key) -> float:
        res = await self.get(key)

        data = res.get("expire_at")
        return (data - datetime.now(timezone.utc)).total_seconds()

    async def get_time_sw(self, key) -> float:

        time = datetime.now(timezone.utc) - timedelta(seconds=self.expire)
        
        res_range = await self.get_range(key,time.timestamp())
        if not res_range:
            return 0.0
        
        timestamp = res_range[0]

        return (timestamp + self.expire) - datetime.now(timezone.utc).timestamp()

    async def cleanup(self,key: str):
        res = self.counter.get(f"sw:{key}")
        if res is None:
        
            return
        now = datetime.now(timezone.utc).timestamp()

        for i in range(len(res) - 1, -1, -1):
            if res[i] < now - self.expire - 1:
                res.pop(i)
    


    async def _clear(self):
        self.counter = dict()
    
    async def close(self):
        pass