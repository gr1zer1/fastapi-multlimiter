from .base import BaseAlgorithm
from asynclimiter.backend import BaseBackend
from typing import Callable
from datetime import datetime,timezone


class TokenBucketAlgorithm(BaseAlgorithm):
    
    
    def __init__(self, backend: BaseBackend, capacity: int, refill_rate: float, key_func: Callable | None = None):
        """Initialize a token bucket limiter.

        Args:
            backend: Storage backend for counters.
            capacity: Maximum allowed amount of tokens in bucket.
            refill_rate: How many tokens puts in bucket per second.
            key_func: Optional callable that builds a key from the request.
        """
        self.backend = backend
        backend.expire = int(refill_rate)
    
        self.limit = capacity
        self.refill_rate = refill_rate

        self.key_func = key_func
    

    async def check(self, key: str) -> dict:
        date = datetime.now(timezone.utc).timestamp()

        return await self.backend.consume_token(
            key=key,
            capacity=self.limit,
            refill_rate=self.refill_rate,
            now=date
        )