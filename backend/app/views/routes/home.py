from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.config import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home_view(request: Request) -> HTMLResponse:
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request, name="pages/home.html", context={"theme": theme}
    )


@router.get("/health-check/")
async def health_check() -> bool:
    return True
