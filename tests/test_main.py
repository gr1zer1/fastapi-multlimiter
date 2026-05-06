from httpx import ASGITransport, AsyncClient
from app.main import app


async def test():
    assert 2 == 2


async def test_root():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


async def test_limit():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        for i in range(5):
            response = await ac.get("/")
            assert response.status_code == 200
        
        response = await ac.get("/")

        assert response.status_code == 429
   