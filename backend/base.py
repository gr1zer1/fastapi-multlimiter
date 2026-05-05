from abc import ABC, abstractmethod
from typing import Any


class BaseBackend(ABC):
    @abstractmethod
    async def get(self,key:str) -> int: ...


    @abstractmethod
    async def put(self,key: str, expire: int): ...


    @abstractmethod
    async def increment(self,key: str) -> int: ...