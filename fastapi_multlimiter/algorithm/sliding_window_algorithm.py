from .base import BaseAlgorithm
from fastapi_multlimiter.backend import BaseBackend
from datetime import datetime,timezone
from typing import Callable


class SlidingWindowAlgorithm(BaseAlgorithm):
    """Sliding-window rate limiting algorithm.

    Tracks request timestamps and counts only requests inside the latest
    rolling time window.
    """

    def __init__(self, backend: BaseBackend, limit: int, window: int, key_func: Callable | None = None):
        """Initialize a sliding-window limiter.

        Args:
            backend: Storage backend for request timestamps.
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
        """Record a request and check whether ``key`` is still under the limit.

        Returns:
            A dictionary containing:
            ``check``: whether the request is allowed,
            ``remain``: remaining requests in the current rolling window,
            ``after``: seconds until the next request slot is available.
        """
        await self.backend.append(key,datetime.now(timezone.utc).timestamp())
        res = await self.backend.get_range(key=key,from_time=datetime.now(timezone.utc).timestamp()-self.window)
        if len(res) > self.limit:
            return {"remain":0,"check":False,"after":await self.backend.get_time_sw(key)}

        
        return {"remain":self.limit - len(res),"check":True,"after":await self.backend.get_time_sw(key)}
        
