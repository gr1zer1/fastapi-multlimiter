from httpx import ASGITransport, AsyncClient
from fastapi import Depends, FastAPI, Request
import pytest_asyncio

from algorithm import FixedWindowAlgorithm, SlidingWindowAlgorithm
from backend import MemoryBackend, RedisBackend
from freezegun import freeze_time
from datetime import datetime,timedelta,timezone
import asyncio

LIMIT = 5


def get_user(request: Request):
    return request.client.host + request.url.path

@pytest_asyncio.fixture
async def app():
    redis_backend = RedisBackend("redis://localhost:6379")

    algorithm_fw = FixedWindowAlgorithm(
        MemoryBackend(),
        limit=LIMIT,
        window=60,
    )
    algorithm_sw = SlidingWindowAlgorithm(
        MemoryBackend(),
        limit=LIMIT,
        window=60,
    )
    redis_fw = FixedWindowAlgorithm(
        redis_backend,
        limit=LIMIT,
        window=5,
    )
    redis_sw = SlidingWindowAlgorithm(
        redis_backend,
        limit=LIMIT,
        window=5,
    )

    with_key_func_sw = SlidingWindowAlgorithm(
        MemoryBackend(),
        limit=5,
        window=60,
        key_func=get_user
    )

    test_app = FastAPI()
    test_app.state.redis_backend = redis_backend

    @test_app.get("/")
    async def root():
        return {"message": "Hello World"}

    @test_app.get("/fw", dependencies=[Depends(algorithm_fw.limiter)])
    async def fw():
        return {"message": "Hello World"}

    @test_app.get("/sw", dependencies=[Depends(algorithm_sw.limiter)])
    async def sw():
        return {"message": "Hello World"}

    @test_app.get("/wrapper/sw")
    @algorithm_sw.limiter_wrapper
    async def wrapper_sw(request: Request):
        return {"message": "Hello World"}

    @test_app.get("/wrapper/fw")
    @algorithm_fw.limiter_wrapper
    async def wrapper_fw(request: Request):
        return {"message": "Hello World"}
    
    @test_app.get("/wrapper/params/fw")
    @algorithm_fw.limiter_wrapper
    async def params_fw(request: Request,name: str):
        return {"message": f"Hello {name}"}

    @test_app.get("/redis/fw", dependencies=[Depends(redis_fw.limiter)])
    async def redis__fw():
        return {"message": "Hello World"}

    @test_app.get("/redis/sw", dependencies=[Depends(redis_sw.limiter)])
    async def redis__sw():
        return {"message": "Hello World"}
    
    @test_app.get("/host/path",dependencies=[Depends(with_key_func_sw.limiter)])
    async def key_sw():
        return {"message": "Hello World"}
        

    yield test_app

    await redis_backend.close()


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def clean_redis(app):
    await app.state.redis_backend._clear()
    yield
    await app.state.redis_backend._clear()





async def limit_loop(url: str, client: AsyncClient, limit: int = 5):
    for _ in range(limit):
        response = await client.get(url)
        assert response.status_code == 200

    response = await client.get(url)
    assert response.status_code == 429
    return response


async def test():
    assert 2 == 2


async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


async def test_limit_sw(client):
    await limit_loop("/sw", client)


async def test_limit_fw(client):
    await limit_loop("/fw", client)


async def test_limit_wrapper_fw(client):
    await limit_loop("/wrapper/fw", client)


async def test_limit_wrapper_sw(client):
    await limit_loop("/wrapper/sw", client)


async def test_wrapper_params(client):
    await limit_loop("/wrapper/params/fw?name=test",client)


async def test_redis_fw(client, clean_redis):
    await limit_loop("/redis/fw", client)


async def test_redis_sw(client, clean_redis):
    await limit_loop("/redis/sw", client)


async def test_timestamp_fw(client,clean_redis):
    await limit_loop("/fw",client)

    date = datetime.now(timezone.utc) + timedelta(seconds=60)
    time = freeze_time(date)
    with time:
        await limit_loop("/fw",client)

async def test_timestamp_sw(client,clean_redis):
    await limit_loop("/sw",client)

    date = datetime.now(timezone.utc) + timedelta(seconds=60)

    time = freeze_time(date)
    with time:
        await limit_loop("/sw",client)



async def test_timestamp_redis_fw(client,clean_redis):
    await limit_loop("/redis/fw",client)

    await asyncio.sleep(5)
    
    await limit_loop("/redis/fw",client)


async def test_timestamp_redis_sw(client,clean_redis):
    await limit_loop("/redis/sw",client)

    await asyncio.sleep(5)
    
    await limit_loop("/redis/sw",client)


async def test_key_func_sw(client):
    await limit_loop("/host/path",client)


async def test_response_headers(client,clean_redis):

    response = await limit_loop("/fw",client)
    assert response.headers.get("X-RateLimit-Limit") == str(LIMIT)
    assert response.headers.get("X-RateLimit-Remaining") == "0"
    assert response.headers.get("Retry-After") is not None