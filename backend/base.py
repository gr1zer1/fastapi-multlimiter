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


    @abstractmethod
    async def append(self,key: str,timestamp: float): ...


    @abstractmethod
    async def get_range(self,key: str, from_time: float) -> list[float]: ...