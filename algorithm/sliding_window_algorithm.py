from .base import BaseAlgorithm
from backend import BaseBackend
from datetime import datetime,timezone
from typing import Callable


class SlidingWindowAlgorithm(BaseAlgorithm):
    def __init__(self, backend: BaseBackend, limit: int, window: int, key_func: Callable | None = None):
        self.backend = backend
        backend.expire = window
    
        self.limit = limit
        self.window = window
        self.key_func = key_func


    async def check(self, key: str) -> dict:
        await self.backend.append(key,datetime.now(timezone.utc).timestamp())
        res = await self.backend.get_range(key=key,from_time=datetime.now(timezone.utc).timestamp()-self.window)
        if len(res) > self.limit:
            return {"remain":0,"check":False,"after":await self.backend.get_time_sw(key)}

        
        return {"remain":self.limit - len(res),"check":True,"after":await self.backend.get_time_sw(key)}
        