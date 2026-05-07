from .base import BaseAlgorithm
from backend import BaseBackend
from datetime import datetime,timezone


class SlidingWindowAlgorithm(BaseAlgorithm):
    def __init__(self, backend: BaseBackend, limit: int, window: int):
        self.backend = backend
        backend.expire = window
    
        self.limit = limit
        self.window = window


    async def check(self, key: str) -> bool: 
        res = await self.backend.get_range(key=key,from_time=datetime.now(timezone.utc).timestamp()-self.window)
        if len(res) >= self.limit:
            await self.backend.append(key,datetime.now(timezone.utc).timestamp())
            return False
        
        await self.backend.append(key,datetime.now(timezone.utc).timestamp())
        
        return True