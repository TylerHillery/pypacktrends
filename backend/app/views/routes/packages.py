from typing import Annotated

from fastapi import APIRouter, Request, Response, Form, Header
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from app.core.config import templates
from app.core.db import read_engine
from app.utils import generate_push_url, parse_packages, generate_chart

router = APIRouter()


@router.get("/packages-list", response_class=HTMLResponse)
async def get_packages_list(
    request: Request,
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    current_packages = parse_packages(hx_current_url)

    return templates.TemplateResponse(
        request=request,
        name="fragments/package_list.html",
        context={"packages": current_packages},
    )


@router.post("/packages-list", response_class=HTMLResponse)
async def create_package(
    request: Request,
    package_name: Annotated[str, Form()],
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    package_name = package_name.strip()

    current_packages = parse_packages(hx_current_url)

    current_packages.add(package_name)

    response = templates.TemplateResponse(
        request=request,
        name="fragments/package_line_item.html",
        context={"package_name": package_name},
    )

    response.headers["HX-Push-Url"] = generate_push_url(current_packages)

    return response


@router.delete("/packages-list", response_class=HTMLResponse)
async def delete_package(
    package_name: str,
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    package_name = package_name.strip()

    current_packages = parse_packages(hx_current_url)

    current_packages.remove(package_name)

    response = Response(
        content="",
        media_type="text/html",
    )

    response.headers["HX-Push-Url"] = generate_push_url(current_packages)
    print(response.headers)

    return response


@router.get("/packages-graph", response_class=HTMLResponse)
async def list_packages(
    request: Request,
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    current_packages = parse_packages(hx_current_url)
    content = generate_chart(current_packages).to_html() if current_packages else ""
    return Response(content=content, media_type="text/html")
