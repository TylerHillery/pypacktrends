from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.core.logger import logger
from app.core.templates import templates

router: APIRouter = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home_view(request: Request) -> HTMLResponse:
    logger.info(
        f"Home page requested from {request.client.host} with theme cookie: {request.cookies.get('theme', 'light')}"
    )
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="pages/home.html",
        context={"theme": theme, "environment": settings.ENVIRONMENT},
    )


@router.get("/health-check/")
async def health_check() -> bool:
    return True
