from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.logger import logger
from app.main import templates

router: APIRouter = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home_view(request: Request) -> HTMLResponse:
    logger.info(
        f"Home page requested from {request.client.host} with theme cookie: {request.cookies.get('theme', 'light')}"
    )
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request, name="pages/home.html", context={"theme": theme}
    )


@router.get("/health-check/")
async def health_check() -> bool:
    return True
