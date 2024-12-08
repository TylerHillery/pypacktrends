import sentry_sdk
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.views.main import api_router

if settings.SENTRY_DSN and settings.ENVIRONMENT != "dev":
    sentry_sdk.init(
        dsn=str(settings.SENTRY_DSN),
        enable_tracing=True,
        traces_sample_rate=1.0,
        _experiments={
            "continuous_profiling_auto_start": True,
        },
    )

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
