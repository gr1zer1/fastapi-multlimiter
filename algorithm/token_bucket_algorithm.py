from .base import BaseAlgorithm
from backend import BaseBackend
from typing import Callable


class TokenBucketAlgorithm(BaseAlgorithm):
    
    
    def __init__(self, backend: BaseBackend, limit: int, window: int, key_func: Callable | None = None):
        """Initialize a token bucket limiter.

        Args:
            backend: Storage backend for counters.
            limit: Maximum number of requests per window.
            window: Window size in seconds.
            key_func: Optional callable that builds a key from the request.
        """
        self.backend = backend
        backend.expire = window
    
        self.limit = limit
        self.window = window

        self.key_func = key_func
