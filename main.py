from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse

from algorithm import FixedWindowAlgorithm
from backend import MemoryBackend


app = FastAPI()

algorithm = FixedWindowAlgorithm(
    MemoryBackend(),
    5,
    60
)


@app.get("/")
async def root():
    return "Hello World"


@app.middleware("http")
async def limiter(request: Request,call_next):
    user_id = request.client.host
    print(request.client.host)
    if await algorithm.check(user_id):
        return await call_next(request)
    
    return JSONResponse(
        status_code=429,
        content={"detail": "Too Many Requests"}
    )