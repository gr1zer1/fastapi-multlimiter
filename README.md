# FastAPI Limiter

Async rate limiter for FastAPI with pluggable backends and algorithms.

## Features

- Three rate limiting algorithms: fixed-window, sliding-window, token bucket
- Two backends: in-memory (for development and tests) and Redis (for production)
- Two usage styles: FastAPI `Depends` and decorator
- Custom key functions (by IP, user, path, or any combination)
- Rate limit response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`
- GitHub Actions CI with Redis service

## Project Structure

```text
.
├── algorithm/
│   ├── base.py
│   ├── fixed_window_algorithm.py
│   ├── sliding_window_algorithm.py
│   └── token_bucket_algorithm.py
├── backend/
│   ├── base.py
│   ├── memory_backend.py
│   └── redis_backend.py
├── tests/
│   └── test_main.py
├── main.py
├── pytest.ini
├── requirements.txt
└── .github/workflows/ci.yml
```

## Requirements

- Python 3.11+
- Redis — required only for Redis-backed routes and Redis tests

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Redis

```bash
docker run --rm -p 6379:6379 redis:7
```

## Running the App

```bash
uvicorn main:app --reload
```

## Demo Endpoints

```text
GET /                  No limiter
GET /fw                Fixed-window, MemoryBackend
GET /sw                Sliding-window, MemoryBackend
GET /wrapper/fw        Fixed-window as decorator
GET /wrapper/sw        Sliding-window as decorator
GET /redis/fw          Fixed-window, RedisBackend
GET /redis/sw          Sliding-window, RedisBackend
GET /redis/tb          Token bucket, RedisBackend
```

Limit is `5` requests per window. Exceeding it returns HTTP `429 Too Many Requests` with headers:

```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
Retry-After: 42.0
```

## Usage

### Dependency style

```python
from fastapi import Depends, FastAPI
from algorithm import FixedWindowAlgorithm
from backend import MemoryBackend

app = FastAPI()

limiter = FixedWindowAlgorithm(
    backend=MemoryBackend(),
    limit=5,
    window=60,
)

@app.get("/limited", dependencies=[Depends(limiter.limiter)])
async def limited():
    return {"message": "ok"}
```

### Decorator style

```python
from fastapi import FastAPI, Request
from algorithm import SlidingWindowAlgorithm
from backend import MemoryBackend

app = FastAPI()

limiter = SlidingWindowAlgorithm(
    backend=MemoryBackend(),
    limit=5,
    window=60,
)

@app.get("/limited")
@limiter.limiter_wrapper
async def limited(request: Request):
    return {"message": "ok"}
```

### Token bucket

```python
from algorithm import TokenBucketAlgorithm
from backend import RedisBackend

limiter = TokenBucketAlgorithm(
    backend=RedisBackend("redis://localhost:6379"),
    capacity=10,
    refill_rate=2.0,  # tokens per second
)

@app.get("/limited", dependencies=[Depends(limiter.limiter)])
async def limited():
    return {"message": "ok"}
```

### Custom key function

```python
from fastapi import Request

def get_user_key(request: Request) -> str:
    return request.headers.get("X-User-ID") or request.client.host

limiter = FixedWindowAlgorithm(
    backend=MemoryBackend(),
    limit=5,
    window=60,
    key_func=get_user_key,
)
```

### Redis backend

```python
from backend import RedisBackend

backend = RedisBackend("redis://localhost:6379")
```

## Running Tests

```bash
docker run --rm -p 6379:6379 redis:7
pytest
```

## Known Limitations

- Sliding-window `zadd` + `zrangebyscore` in `RedisBackend` are not atomic — consider a Lua script for high-concurrency scenarios

## License

MIT. See [LICENSE](LICENSE).