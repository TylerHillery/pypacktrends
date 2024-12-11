import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logger import logger
from app.metrics import metrics_collection_task, start_metrics_server
from app.views.main import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(
        f"Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} environment"
    )
    start_metrics_server()
    app.state.metrics_task = asyncio.create_task(metrics_collection_task())
    yield
    if hasattr(app.state, "metrics_task"):
        app.state.metrics_task.cancel()
        try:
            await app.state.metrics_task
        except asyncio.CancelledError:
            pass


if settings.SENTRY_DSN and settings.ENVIRONMENT != "dev":
    logger.info("Initializing Sentry SDK")
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN),
        enable_tracing=True,
        traces_sample_rate=1.0,
        _experiments={
            "continuous_profiling_auto_start": True,
        },
    )

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(api_router)

try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except Exception as e:
    logger.error(f"Failed to mount static files directory: {str(e)}")
