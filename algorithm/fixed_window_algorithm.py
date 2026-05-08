from .base import BaseAlgorithm
from backend import BaseBackend
from datetime import datetime,timezone


class FixedWindowAlgorithm(BaseAlgorithm):


    def __init__(self, backend: BaseBackend, limit: int, window: int):
        self.backend = backend
        backend.expire = window
    
        self.limit = limit
        self.window = window

    
    async def check(self, key: str) -> bool:
        payload = await self.backend.put(key)
        print(payload["counter"])

        return payload["counter"] <= self.limit