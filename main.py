from fastapi import FastAPI,Request,Depends
from fastapi.responses import JSONResponse

from contextlib import asynccontextmanager

from asynclimiter import FixedWindowAlgorithm,SlidingWindowAlgorithm
from asynclimiter import MemoryBackend,RedisBackend

redis_backend = RedisBackend("redis://localhost:6379")

algorithm_fw = FixedWindowAlgorithm(
    MemoryBackend(),
    5,
    60
)

algorithm_sw = SlidingWindowAlgorithm(
    MemoryBackend(),
    5,
    60
)

redis_fw = FixedWindowAlgorithm(

    redis_backend,
    5,
    60
)

redis_sw = SlidingWindowAlgorithm(
    redis_backend,
    5,
    60
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await redis_fw.backend.close()
    await redis_sw.backend.close()


app = FastAPI(lifespan=lifespan)



@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/fw",dependencies=[Depends(algorithm_fw.limiter)])
async def fw():
    return {"message": "Hello World"}


@app.get("/sw",dependencies=[Depends(algorithm_sw.limiter)])
async def sw():
    return {"message": "Hello World"}

@app.get("/wrapper/sw")
@algorithm_sw.limiter_wrapper
async def wrapper_sw(request: Request):
    return {"message": "Hello World"}


@app.get("/wrapper/fw")
@algorithm_fw.limiter_wrapper
async def wrapper_fw(request: Request):
    return {"message": "Hello World"}

@app.get("/redis/fw",dependencies=[Depends(redis_fw.limiter)])
async def redis__fw():
    return {"message": "Hello World"}

@app.get("/redis/sw",dependencies=[Depends(redis_sw.limiter)])
async def redis__sw():
    return {"message": "Hello World"}