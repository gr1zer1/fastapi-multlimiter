from .base import BaseAlgorithm
from backend import BaseBackend
from datetime import datetime,timezone


class FixedWindowAlgorithm(BaseAlgorithm):


    def __init__(self, backend: BaseBackend, limit: int, window: int):
        self.backend = backend
        backend.expire = limit
    
        self.limit = limit
        self.window = window

    
    async def check(self, key: str) -> bool:
        payload = await self.backend.get(key)
        if payload is None:
            self.backend.put(key)
            return True
        elif self.limit < payload["counter"]:
            self.backend.increment(key)
            return False
        else:
            self.backend.increment(key)
            return True
        
        