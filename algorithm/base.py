from abc import ABC,abstractmethod
from backend import BaseBackend


class BaseAlgorithm(ABC):
    
    def __init__(self,backend: BaseBackend,limit: int, window: int):
        self.backend = backend
        self.limit = limit
        self.window = window
    

    @abstractmethod
    async def check(self, key: str) -> bool: ...