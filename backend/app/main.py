from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.logger import logger
from app.views.main import api_router

templates = Jinja2Templates(directory="app/templates")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(
        f"Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} environment"
    )
    yield


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
