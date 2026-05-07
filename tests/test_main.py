from httpx import ASGITransport, AsyncClient
from main import app,algorithm_sw,algorithm_fw
import pytest_asyncio


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


async def test():
    assert 2 == 2


async def test_root(client):
    
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


async def test_limit_sw(client):
    
    for i in range(5):
        response = await client.get("/sw")
        assert response.status_code == 200
        
    response = await client.get("/sw")

    assert response.status_code == 429


async def test_limit_fw(client):
    for i in range(5):
        response = await client.get("/fw")
        assert response.status_code == 200
        
    response = await client.get("/fw")

    assert response.status_code == 429


async def test_limit_wrapper_fw(client):
    for i in range(5):
        response = await client.get("/wrapper/fw")
        print(response.json())
        assert response.status_code == 200
        
    response = await client.get("/wrapper/fw")

    assert response.status_code == 429


async def test_limit_wrapper_sw(client):
    for i in range(5):
        response = await client.get("/wrapper/sw")
        assert response.status_code == 200
        
    response = await client.get("/wrapper/sw")

    assert response.status_code == 429