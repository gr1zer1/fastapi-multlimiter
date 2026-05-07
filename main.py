from fastapi import FastAPI,Request,Depends
from fastapi.responses import JSONResponse

from algorithm import FixedWindowAlgorithm,SlidingWindowAlgorithm
from backend import MemoryBackend


app = FastAPI()

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


# @app.middleware("http")
# async def limiter(request: Request,call_next):
#     user_id = request.client.host
#     print(request.client.host)
#     if await algorithm.check(user_id):
#         return await call_next(request)
    
#     return JSONResponse(
#         status_code=429,
#         content={"detail": "Too Many Requests"}
#     )