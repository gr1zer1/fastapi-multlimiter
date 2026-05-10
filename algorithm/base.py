from abc import ABC,abstractmethod
from backend import BaseBackend
from fastapi import Request,HTTPException,status
from typing import Callable
import inspect

from functools import wraps
import inspect


class BaseAlgorithm(ABC):
    
    def __init__(self,backend: BaseBackend,limit: int, window: int, key_func: Callable | None = None):
        self.backend = backend
        self.limit = limit
        self.window = window
        self.key_func: Callable | None = key_func
    

    @abstractmethod
    async def check(self, key: str) -> dict: ...


    async def get_value(self,request: Request) -> str:
        if self.key_func is None:
            return request.client.host
        
        elif inspect.iscoroutinefunction(self.key_func):
            return await self.key_func(request)
        
        return self.key_func(request)


    async def limiter(self, request: Request):
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
        @wraps(func)
        async def wrapper(request: Request, **kwargs):

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