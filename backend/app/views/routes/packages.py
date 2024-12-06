from typing import Annotated

from fastapi import APIRouter, Request, Form, Header
from fastapi.responses import HTMLResponse, JSONResponse

from app.core.config import templates
from app.models import TimeRangeModel

from app.utils import (
    generate_altair_colors,
    generate_push_url,
    parse_url_params,
    generate_chart,
    validate_package,
)

router = APIRouter()


@router.get("/package-list", response_class=HTMLResponse)
async def get_package_list(
    request: Request,
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    current_packages, _ = parse_url_params(hx_current_url)
    colors = generate_altair_colors(len(current_packages))

    package_data = [
        {"name": name, "color": color} for name, color in zip(current_packages, colors)
    ]

    return templates.TemplateResponse(
        request=request,
        name="fragments/package_list.html",
        context={"package_data": package_data},
    )


@router.post("/package-list", response_class=HTMLResponse)
async def create_package(
    request: Request,
    package_name: Annotated[str, Form()],
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    package_name = package_name.strip()
    current_packages, current_time_range = parse_url_params(hx_current_url)

    if package_name in current_packages:
        return JSONResponse(
            status_code=409, content={"error": f"'{package_name}' already selected"}
        )

    if not validate_package(package_name):
        return JSONResponse(
            status_code=422, content={"error": f"'{package_name}' not found on PyPI"}
        )

    current_packages.append(package_name)

    return templates.TemplateResponse(
        request=request,
        name="fragments/package_line_item.html",
        context={
            "package_name": package_name,
            "color": generate_altair_colors(len(current_packages))[-1],
        },
        headers={"HX-Push-Url": generate_push_url(current_packages, current_time_range)},
    )


@router.delete("/package-list", response_class=HTMLResponse)
async def delete_package(
    request: Request,
    package_name: str,
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    package_name = package_name.strip()
    current_packages, current_time_range = parse_url_params(hx_current_url)
    current_packages.remove(package_name)
    colors = generate_altair_colors(len(current_packages))

    package_data = [
        {"name": name, "color": color} for name, color in zip(current_packages, colors)
    ]

    return templates.TemplateResponse(
        request=request,
        name="fragments/package_list.html",
        context={"package_data": package_data},
        headers={"HX-Push-Url": generate_push_url(current_packages, current_time_range)},
    )


@router.get("/packages-graph", response_class=HTMLResponse)
async def list_packages(
    request: Request,
    time_range: str | None = None,
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    theme = request.cookies.get("theme", "light")
    current_packages, current_time_range = parse_url_params(hx_current_url)

    # TODO: error handeling
    time_range = TimeRangeModel(value=time_range) if time_range is not None else TimeRangeModel(value=current_time_range)

    if len(current_packages) < 1:
        return HTMLResponse("")

    return templates.TemplateResponse(
        request=request,
        name="fragments/chart.html",
        context={
            "chart": generate_chart(current_packages, time_range, theme).to_html(),
            "time_range": time_range.value,
        },
        headers={"HX-Push-Url": generate_push_url(current_packages, time_range.value)},
    )
