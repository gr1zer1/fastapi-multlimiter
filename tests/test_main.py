from httpx import ASGITransport, AsyncClient
from main import app,algorithm_sw,algorithm_fw
import pytest_asyncio
import asyncio


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest_asyncio.fixture(autouse=True)
async def reset_backend():
    yield
    await algorithm_fw.backend._clear()
    await algorithm_sw.backend._clear()


async def limit_loop(url:str,client:AsyncClient):
    for i in range(5):
        response = await client.get(url)
        assert response.status_code == 200
        
    response = await client.get(url)

    assert response.status_code == 429


async def test():
    assert 2 == 2


async def test_root(client):
    
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


async def test_limit_sw(client):
    
    await limit_loop("/sw",client)


async def test_limit_fw(client):
    await limit_loop("/fw",client)


async def test_limit_wrapper_fw(client):
    await limit_loop("/wrapper/fw",client)


async def test_limit_wrapper_sw(client):
    await limit_loop("/wrapper/sw",client)


async def test_timestamp_fw(client):
    await limit_loop("/fw",client)

    await asyncio.sleep(60)
    print(algorithm_fw.backend.counter)
    await limit_loop("/fw",client)


async def test_timestamp_sw(client):
    await limit_loop("/sw",client)

    await asyncio.sleep(60)
    print(algorithm_fw.backend.counter)
    await limit_loop("/sw",client)