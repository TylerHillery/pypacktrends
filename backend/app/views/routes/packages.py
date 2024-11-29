from typing import Annotated
from urllib.parse import urlencode, urlparse, parse_qs

from fastapi import APIRouter, Request, Response, Form, Header
from fastapi.responses import HTMLResponse

from app.core.config import templates

router = APIRouter()


@router.get("/packages", response_class=HTMLResponse)
async def list_packages(
    request: Request,
    hx_current_url: Annotated[str | None, Header(alias="HX-Current-URL")] = None,
):
    current_packages = []

    if hx_current_url:
        parsed_url = urlparse(hx_current_url)
        query_params = parse_qs(parsed_url.query)
        current_packages = query_params.get('packages', [])

    return templates.TemplateResponse(
        request=request,
        name="components/package_list.html",
        context={"packages": current_packages},
    )

@router.post("/packages", response_class=HTMLResponse)
async def create_package(
    request: Request,
    package_name: Annotated[str, Form()],
    hx_current_url: Annotated[str | None, Header(alias="HX-Current-URL")] = None,
):
    current_packages = []
    if hx_current_url:
        parsed_url = urlparse(hx_current_url)
        query_params = parse_qs(parsed_url.query)
        current_packages = query_params.get('packages', [])

    if package_name not in current_packages:
        current_packages.append(package_name)

    response = templates.TemplateResponse(
        request=request,
        name="components/package_line_item.html",
        context={"package_name": package_name},
    )

    response.headers["HX-Push-Url"] = (
        f"?{urlencode({'packages': current_packages}, doseq=True)}"
    )
    return response


@router.delete("/packages", response_class=HTMLResponse)
async def delete_package(
    request: Request,
    package_name: str,
    hx_current_url: Annotated[str | None, Header(alias="HX-Current-URL")] = None,
):
    current_packages = []
    if hx_current_url:
        parsed_url = urlparse(hx_current_url)
        query_params = parse_qs(parsed_url.query)
        current_packages = query_params.get('packages', [])

    if package_name in current_packages:
        current_packages.remove(package_name)

    response = Response(
        content="",
        media_type="text/html",
    )

    response.headers["HX-Push-Url"] = (
        f"?{urlencode({'packages': current_packages}, doseq=True)}"
    )

    return response
