from abc import ABC,abstractmethod
from fastapi_multlimiter.backend import BaseBackend
from fastapi import Request,HTTPException,status
from typing import Callable
import inspect

from functools import wraps
import inspect


class BaseAlgorithm(ABC):
    """Base class for FastAPI-compatible rate limiting algorithms.

    Args:
        backend: Storage backend used by the algorithm.
        limit: Maximum number of requests allowed in the window.
        window: Window size in seconds.
        key_func: Optional callable that builds a rate limit key from a request.
    """
    
    def __init__(self,backend: BaseBackend,limit: int, window: int, key_func: Callable | None = None):
        """Initialize common limiter configuration."""
        self.backend = backend
        self.limit = limit
        self.window = window
        self.key_func: Callable | None = key_func
    

    @abstractmethod
    async def check(self, key: str) -> dict:
        """Check whether a key is allowed to make a request.

        Returns:
            A dictionary with ``check``, ``remain``, and ``after`` fields.
        """
        ...


    async def get_value(self,request: Request) -> str:
        """Build a rate limit key for a FastAPI request."""
        if self.key_func is None:
            return request.client.host
        
        elif inspect.iscoroutinefunction(self.key_func):
            return await self.key_func(request)
        
        return self.key_func(request)


    async def limiter(self, request: Request):
        """FastAPI dependency that raises HTTP 429 when the limit is exceeded."""
        res = await self.check(await self.get_value(request))
        if not res["check"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"detail": "Too Many Requests"},
                headers={
                    "X-RateLimit-Limit":str(self.limit),
                    "X-RateLimit-Remaining":str(res["remain"]),
                    "Retry-After":str(res["after"])
                    },
            )
        
    


    def limiter_wrapper(self, func):
        """Return a route decorator that applies this rate limiter."""
        @wraps(func)
        async def wrapper(request: Request, **kwargs):
            """Check the request limit before calling the wrapped route handler."""

            res = await self.check(await self.get_value(request))
            if not res["check"]:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={"detail": "Too Many Requests"},
                    headers={
                        "X-RateLimit-Limit": str(self.limit),
                        "X-RateLimit-Remaining": str(res["remain"]),
                        "Retry-After": str(res["after"])
                    },
                )
            return await func(request,**kwargs)
        
        return wrapper
