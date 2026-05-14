from .base import BaseAlgorithm
from fastapi_multlimiter.backend import BaseBackend
from typing import Callable


class FixedWindowAlgorithm(BaseAlgorithm):
    """Fixed-window rate limiting algorithm.

    Counts requests in a fixed time window. When the window expires, the
    counter resets and the key can make requests again.
    """


    def __init__(self, backend: BaseBackend, limit: int, window: int, key_func: Callable | None = None):
        """Initialize a fixed-window limiter.

        Args:
            backend: Storage backend for counters.
            limit: Maximum number of requests per window.
            window: Window size in seconds.
            key_func: Optional callable that builds a key from the request.
        """
        self.backend = backend
        backend.expire = window
    
        self.limit = limit
        self.window = window

        self.key_func = key_func

    
    async def check(self, key: str) -> dict:
        """Check and increment the fixed-window counter for ``key``.

        Returns:
            A dictionary containing:
            ``check``: whether the request is allowed,
            ``remain``: remaining requests in the current window,
            ``after``: seconds until the limit resets.
        """
        payload = await self.backend.put(key)

        if payload["counter"] <= self.limit:
            return {"remain":self.limit - payload["counter"],"check":True,"after":await self.backend.get_time_fw(key)}
        
        return {"remain":0,"check":False,"after":await self.backend.get_time_fw(key)}
