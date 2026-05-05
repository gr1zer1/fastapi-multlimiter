from abc import ABC, abstractmethod
from typing import Any


class BaseBackend(ABC):
    expire: int | None = None

    @abstractmethod
    async def get(self,key:str) -> dict | None: ...


    @abstractmethod
    async def put(self,key: str): ...


    @abstractmethod
    async def increment(self,key: str) -> int | dict: ...