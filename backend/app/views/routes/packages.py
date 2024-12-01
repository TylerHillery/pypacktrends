from typing import Annotated

from fastapi import APIRouter, Request, Form, Header
from fastapi.responses import HTMLResponse, JSONResponse

from app.core.config import templates
from app.utils import (
    generate_altair_colors,
    generate_push_url,
    parse_packages,
    generate_chart,
    validate_package,
)

router = APIRouter()


@router.get("/package-list", response_class=HTMLResponse)
async def get_package_list(
    request: Request,
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    current_packages = parse_packages(hx_current_url)

    return templates.TemplateResponse(
        request=request,
        name="fragments/package_list.html",
        context={
            "packages": current_packages,
        },
    )


@router.post("/package-list", response_class=HTMLResponse)
async def create_package(
    request: Request,
    package_name: Annotated[str, Form()],
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    package_name = package_name.strip()
    current_packages = parse_packages(hx_current_url)

    if package_name in current_packages:
        return JSONResponse(
            status_code=409, content={"error": f"'{package_name}' already selected"}
        )

    if not validate_package(package_name):
        return JSONResponse(
            status_code=422, content={"error": f"'{package_name}' not found on PyPI"}
        )

    current_packages.append(package_name)

    print("COLORS", generate_altair_colors(len(current_packages)))

    return templates.TemplateResponse(
        request=request,
        name="fragments/package_line_item.html",
        context={
            "package_name": package_name,
            "color": generate_altair_colors(len(current_packages))[-1],
        },
        headers={"HX-Push-Url": generate_push_url(current_packages)},
    )


@router.delete("/package-list", response_class=HTMLResponse)
async def delete_package(
    package_name: str,
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    package_name = package_name.strip()
    current_packages = parse_packages(hx_current_url)
    current_packages.remove(package_name)

    return HTMLResponse(
        content="", headers={"HX-Push-Url": generate_push_url(current_packages)}
    )


@router.get("/packages-graph", response_class=HTMLResponse)
async def list_packages(
    request: Request,
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    current_packages = parse_packages(hx_current_url)
    content = generate_chart(current_packages).to_html() if current_packages else ""
    return HTMLResponse(content=content)
