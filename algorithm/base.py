from abc import ABC,abstractmethod
from backend import BaseBackend
from fastapi import Request
from fastapi import HTTPException,status


class BaseAlgorithm(ABC):
    
    def __init__(self,backend: BaseBackend,limit: int, window: int):
        self.backend = backend
        self.limit = limit
        self.window = window
    

    @abstractmethod
    async def check(self, key: str) -> bool: ...


    async def limiter(self, request: Request):
        if not await self.check(request.client.host):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"detail": "Too Many Requests"}
            )
        