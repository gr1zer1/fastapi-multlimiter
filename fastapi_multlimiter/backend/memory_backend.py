from .base import BaseBackend
from datetime import datetime,timezone,timedelta


class MemoryBackend(BaseBackend):
    """In-memory backend for local development and tests.

    This backend stores counters and timestamps in a Python dictionary.
    Data is not shared between processes and is lost when the process exits.
    """

    expire: int | None = None

    def __init__(self):
        """Create an empty in-memory storage."""
        self.counter: dict[str,dict | list] = dict()
        self.expire: float | None = None


    async def put(self, key: str) -> dict:
        """Create or update a fixed-window counter.

        Args:
            key: Rate limit key.

        Returns:
            Counter payload with ``counter`` and ``expire_at`` fields.
        """
        if await self.get(key) is not None:

            return await self.increment(key)

        payload = {"counter":1,"expire_at":datetime.now(timezone.utc) + timedelta(seconds=self.expire)}

        self.counter[f"fw:{key}"] = payload
        return payload
    

    async def get(self, key: str) -> dict | None:
        """Return fixed-window payload for ``key`` if it exists."""
        return self.counter.get(f"fw:{key}")
    

    async def increment(self, key: str) -> int | dict:
        """Increment fixed-window counter and reset it when expired."""
        res = await self.get(key)
        
        if res is not None:
            if datetime.now(timezone.utc) > res["expire_at"]:
                res["counter"] = 0
                payload = {"counter":0,"expire_at":datetime.now(timezone.utc) + timedelta(seconds=self.expire)}

                self.counter[f"fw:{key}"] = payload

            
            self.counter[f"fw:{key}"]["counter"] +=1
            return self.counter[f"fw:{key}"]
        else:
            return await self.put(key)
    

    async def append(self, key: str, timestamp: float):
        """Append a timestamp to the sliding-window list for ``key``."""
        res = self.counter.get(f"sw:{key}")

        if res is None:

            self.counter[f"sw:{key}"] = [timestamp]
        else:
            self.counter[f"sw:{key}"].append(timestamp)


    async def get_range(self, key: str, from_time: float) -> list[float]:
        """Return sliding-window timestamps newer than ``from_time``."""
        res = self.counter.get(f"sw:{key}")
        if res is None:
            return [] 
        await self.cleanup(key)
        return  list(filter(lambda t: t>from_time,res))
    
    
    async def get_bucket(self, key: str) -> dict | None: 
        """Return token bucket state for ``key`` if it exists."""
        res = self.counter.get(f"tb:{key}")
        return res


    async def set_bucket(self,
                         key: str,
                         tokens: int,
                         last_refill: float
                    ) -> dict:
        """Store token bucket state for ``key``.

        Args:
            key: Rate limit key.
            tokens: Current number of tokens in the bucket.
            last_refill: Timestamp of the latest refill calculation.

        Returns:
            Stored token bucket payload.
        """
        payload = {"tokens":tokens,"last_refill":last_refill}
        
        self.counter[f"tb:{key}"] = payload

        return payload
    
    async def consume_token(self,
                            key: str,
                            capacity: int,
                            refill_rate: float,
                            now: float
                        ) -> dict:
        """Consume one token from an in-memory token bucket.

        The bucket is created on the first request. Existing buckets are
        refilled based on elapsed time before a token is consumed.

        Returns:
            A dictionary containing:
            ``check``: whether the request is allowed,
            ``remain``: remaining tokens in the bucket,
            ``after``: seconds until another token is available.
        """
        res = await self.get_bucket(key)
        
        

        if res is None:
            
            tokens = capacity
            tokens -= 1

            await self.set_bucket(
                key,
                tokens,
                now)
            
            return {"check":True,"remain":tokens,"after":0}

        tokens = res["tokens"]
        last_refill = res["last_refill"]

        if last_refill < now:
            res["tokens"] = min(
                capacity,tokens + (refill_rate * (now-last_refill))
                )
            tokens = res["tokens"]
            res["last_refill"] = now
            last_refill = now

        if tokens < 1:
            retry_after = 1/refill_rate

            return {"check":False,
                    "remain":tokens,
                    "after":retry_after
                    }

        tokens -= 1

        await self.set_bucket(key,tokens,last_refill)
        return {"check":True,"remain":tokens,"after":0}


    
    async def get_time_fw(self, key) -> float:
        """Return seconds until the fixed-window counter for ``key`` resets."""
        res = await self.get(key)

        data = res.get("expire_at")
        return (data - datetime.now(timezone.utc)).total_seconds()

    async def get_time_sw(self, key) -> float:
        """Return seconds until the oldest request leaves the sliding window."""

        time = datetime.now(timezone.utc) - timedelta(seconds=self.expire)
        
        res_range = await self.get_range(key,time.timestamp())
        if not res_range:
            return 0.0
        
        timestamp = res_range[0]

        return (timestamp + self.expire) - datetime.now(timezone.utc).timestamp()

    async def cleanup(self,key: str):
        """Remove expired sliding-window timestamps for ``key``."""
        res = self.counter.get(f"sw:{key}")
        if res is None:
        
            return
        now = datetime.now(timezone.utc).timestamp()

        for i in range(len(res) - 1, -1, -1):
            if res[i] < now - self.expire - 1:
                res.pop(i)
    


    async def _clear(self):
        """Remove all in-memory counters and timestamps."""
        self.counter = dict()
    
    async def close(self):
        """Close the backend.

        Memory backend does not hold external resources, so this is a no-op.
        """
        pass
