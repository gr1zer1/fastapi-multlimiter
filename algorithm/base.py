from abc import ABC,abstractmethod
from backend import BaseBackend
from fastapi import Request,HTTPException,status
from typing import Callable
import inspect


class BaseAlgorithm(ABC):
    
    def __init__(self,backend: BaseBackend,limit: int, window: int, key_func: Callable | None = None):
        self.backend = backend
        self.limit = limit
        self.window = window
        self.key_func: Callable | None = key_func
    

    @abstractmethod
    async def check(self, key: str) -> bool: ...


    async def get_value(self,request: Request) -> str:
        if self.key_func is None:
            return request.client.host
        
        elif inspect.iscoroutinefunction(self.key_func):
            return await self.key_func(request)
        
        return self.key_func(request)


    async def limiter(self, request: Request):
        if not await self.check(await self.get_value(request)):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"detail": "Too Many Requests"}
            )
    
    def limiter_wrapper(self, func):
        async def wrapper(request: Request):
            if not await self.check(await self.get_value(request)):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too Many Requests"
                )
            return await func(request)
        return wrapper