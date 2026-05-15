from .base import BaseAlgorithm
from fastapi_multlimiter.backend import BaseBackend
from typing import Callable
from datetime import datetime,timezone


class TokenBucketAlgorithm(BaseAlgorithm):
    """Token bucket rate limiting algorithm.

    Each key has a bucket with a fixed capacity. Requests consume one token,
    and tokens refill over time according to ``refill_rate``.
    """
    
    
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
        """Consume one token for ``key`` if a token is available.

        Returns:
            A dictionary containing:
            ``check``: whether the request is allowed,
            ``remain``: remaining tokens in the bucket,
            ``after``: seconds until another token is available.
        """
        date = datetime.now(timezone.utc).timestamp()

        return await self.backend.consume_token(
            key=key,
            capacity=self.limit,
            refill_rate=self.refill_rate,
            now=date
        )
