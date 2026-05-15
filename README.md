# fastapi-multlimiter

Async rate limiter for FastAPI with pluggable backends and algorithms.

## Features

- Three rate limiting algorithms: fixed-window, sliding-window, token bucket
- Two backends: in-memory (for development and tests) and Redis (for production)
- Two usage styles: FastAPI `Depends` and decorator
- Custom key functions (by IP, user, path, or any combination)
- Rate limit response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`
- GitHub Actions CI with Redis service

## Requirements

- Python 3.12+
- Redis server — required only for Redis-backed routes and Redis tests

## Installation

Install the package from PyPI:

```bash
pip install fastapi-multlimiter
```

For local development from this repository:

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
from fastapi_multlimiter.algorithm import FixedWindowAlgorithm
from fastapi_multlimiter.backend import MemoryBackend

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
from fastapi_multlimiter.algorithm import SlidingWindowAlgorithm
from fastapi_multlimiter.backend import MemoryBackend

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
from fastapi import Depends
from fastapi_multlimiter.algorithm import TokenBucketAlgorithm
from fastapi_multlimiter.backend import RedisBackend

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
from fastapi_multlimiter.backend import RedisBackend

backend = RedisBackend("redis://localhost:6379")
```

## Project Structure

```text
.
├── fastapi_multlimiter/
│   ├── algorithm/
│   │   ├── base.py
│   │   ├── fixed_window_algorithm.py
│   │   ├── sliding_window_algorithm.py
│   │   └── token_bucket_algorithm.py
│   └── backend/
│       ├── base.py
│       ├── memory_backend.py
│       └── redis_backend.py
├── tests/
│   └── test_main.py
├── main.py
├── pyproject.toml
├── pytest.ini
├── requirements.txt
└── .github/workflows/ci.yml
```

## Running Tests

```bash
docker run --rm -p 6379:6379 redis:7
pytest
```

## Publishing

Releases are published to PyPI by GitHub Actions when a version tag is pushed.
The tag must match the package version in `pyproject.toml`.

```bash
git tag v0.1.0
git push origin v0.1.0
```

The workflow uses PyPI Trusted Publishing. Configure a trusted publisher for
this repository on PyPI with workflow file `.github/workflows/publish.yml` and
environment `pypi`.

## Known Limitations

- Sliding-window `zadd` + `zrangebyscore` in `RedisBackend` are not atomic — consider a Lua script for high-concurrency scenarios

## License

MIT. See [LICENSE](LICENSE).
