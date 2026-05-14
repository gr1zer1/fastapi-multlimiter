from abc import ABC, abstractmethod
from typing import Any


class BaseBackend(ABC):
    """Abstract storage backend used by rate limiting algorithms.

    Backend implementations store counters for fixed-window limits and
    timestamps for sliding-window limits.
    """

    expire: int | None = None

    @abstractmethod
    async def get(self,key:str) -> dict | None:
        """Return fixed-window payload for a key, or ``None`` if it does not exist."""
        ...


    @abstractmethod
    async def put(self,key: str):
        """Create or update fixed-window counter payload for a key."""
        ...


    @abstractmethod
    async def increment(self,key: str) -> int | dict:
        """Increment fixed-window counter for a key."""
        ...


    @abstractmethod
    async def append(self,key: str,timestamp: float):
        """Append request timestamp for sliding-window tracking."""
        ...


    @abstractmethod
    async def get_range(self,key: str, from_time: float) -> list[float]:
        """Return sliding-window timestamps newer than ``from_time``."""
        ...

    @abstractmethod
    async def consume_token(self,
                            key: str,
                            capacity: int,
                            refill_rate: float,
                            now: float
                        ) -> dict:
        """
        Get dict with data about token bucket
        Returns:
            A dictionary with ``allowed``, ``tokens_left``, and ``retry_after`` fields.
        """
        ...

    @abstractmethod
    async def get_time_fw(self, key: str) -> float:
        """Return seconds until the fixed-window counter resets."""
        ...

    @abstractmethod
    async def get_time_sw(self, key: str) -> float:
        """Return seconds until the next sliding-window request slot is available."""
        ...


    @abstractmethod
    async def _clear(self):
        """Remove all backend data.

        This method is intended for tests and local development utilities.
        """
        ...

    @abstractmethod
    async def close(self):
        """Close backend connections and release resources."""
        ...
