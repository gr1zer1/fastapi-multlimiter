from .base import BaseAlgorithm
from backend import BaseBackend
from typing import Callable


class FixedWindowAlgorithm(BaseAlgorithm):


    def __init__(self, backend: BaseBackend, limit: int, window: int, key_func: Callable | None = None):
        self.backend = backend
        backend.expire = window
    
        self.limit = limit
        self.window = window

        self.key_func = key_func

    
    async def check(self, key: str) -> dict:
        payload = await self.backend.put(key)

        if payload["counter"] <= self.limit:
            return {"remain":self.limit - payload["counter"],"check":True,"after":await self.backend.get_time_fw(key)}
        
        return {"remain":0,"check":False,"after":await self.backend.get_time_fw(key)}

