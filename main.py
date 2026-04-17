import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import router as task_router
from app.config.settings import settings
from app.db import init_db
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="企业微信 RPA 消息发送器",
    description="客服 Agent 的企业微信桌面消息发送执行器",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(task_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
