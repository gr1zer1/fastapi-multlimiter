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
        res = await self.backend.get_range(key=key,from_time=float(datetime.now(timezone.utc)))
        if len(res) >= self.limit:
            self.backend.append(key,float(datetime.now(timezone.utc)))
            return False
        
        self.backend.append(key,float(datetime.now(timezone.utc)))
        
        return True