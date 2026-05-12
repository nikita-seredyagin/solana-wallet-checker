from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.cache.redis_client import close_redis, init_redis
from app.database import init_db
from app.routers.check import router as check_router
from app.routers.task import router as task_router
from app.routers.wallet import router as wallet_router

STATIC_DIR = Path(__file__).parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis()
    yield
    await close_redis()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(wallet_router)
app.include_router(check_router)
app.include_router(task_router)


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(STATIC_DIR / "index.html")
