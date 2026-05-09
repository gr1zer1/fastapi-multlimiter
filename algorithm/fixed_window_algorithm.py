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

    
    async def check(self, key: str) -> bool:
        payload = await self.backend.put(key)
        print(payload["counter"])

        return payload["counter"] <= self.limit