# FastAPI Limiter

Async rate limiter prototype for FastAPI with fixed-window and sliding-window algorithms.

The project currently includes:

- FastAPI dependency-based limiter usage
- decorator-based limiter usage
- in-memory backend
- Redis backend
- fixed-window algorithm
- sliding-window algorithm
- async tests for memory and Redis flows

## Project Structure

```text
.
├── algorithm/
│   ├── base.py
│   ├── fixed_window_algorithm.py
│   └── sliding_window_algorithm.py
├── backend/
│   ├── base.py
│   ├── memory_backend.py
│   └── redis_backend.py
├── tests/
│   └── test_main.py
├── main.py
├── pytest.ini
└── requirements.txt
```

## Requirements

- Python 3.11+
- Redis, required only for Redis-backed routes and Redis tests

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running Redis

The demo app and tests expect Redis at `redis://localhost:6379`.

With Docker:

```bash
docker run --rm -p 6379:6379 redis:7
```

## Running the App

```bash
uvicorn main:app --reload
```

The app will be available at:

```text
http://127.0.0.1:8000
```

## Demo Endpoints

```text
GET /              No limiter
GET /fw            Fixed-window limiter with MemoryBackend
GET /sw            Sliding-window limiter with MemoryBackend
GET /wrapper/fw    Fixed-window limiter as decorator
GET /wrapper/sw    Sliding-window limiter as decorator
GET /redis/fw      Fixed-window limiter with RedisBackend
GET /redis/sw      Sliding-window limiter with RedisBackend
```

The current demo limit is `5` requests per window. After the limit is exceeded, the app returns HTTP `429 Too Many Requests`.

## Usage Example

Dependency style:

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

Decorator style:

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

Custom key function:

```python
from fastapi import Request


def get_user_key(request: Request) -> str:
    return request.client.host + request.url.path
```

Pass it to an algorithm:

```python
limiter = SlidingWindowAlgorithm(
    backend=MemoryBackend(),
    limit=5,
    window=60,
    key_func=get_user_key,
)
```

## Running Tests

Start Redis first if you want to run the full test suite:

```bash
docker run --rm -p 6379:6379 redis:7
```

Then run:

```bash
pytest
```

or:

```bash
python -m pytest
```

## Current Limitations

This project is still a prototype. Before using it as a reusable package or in production, the main missing pieces are:

- `pyproject.toml` packaging
- CI configuration
- separate unit and integration tests
- atomic Redis operations for concurrent requests
- documented public API

## License

MIT. See [LICENSE](LICENSE).
