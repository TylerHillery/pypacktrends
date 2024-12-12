from typing import Annotated

from fastapi import APIRouter, Form, Header, Request
from fastapi.responses import HTMLResponse

from app.chart import generate_altair_colors, generate_chart
from app.core.logger import logger
from app.main import templates
from app.models import TimeRangeValidValues
from app.utils import (
    generate_hx_push_url,
    parse_query_params,
    validate_package,
)

router: APIRouter = APIRouter()


@router.get("/package-list", response_class=HTMLResponse)
async def get_package_list(
    request: Request,
    url: Annotated[str, Header(alias="HX-Current-URL")],
) -> HTMLResponse:
    logger.info(f"Fetching package list from URL: {url}")
    query_params = parse_query_params(url)
    package_data = []
    if query_params.packages:
        colors = generate_altair_colors(len(query_params.packages))
        for package, color in zip(query_params.packages, colors):
            package_data.append({"name": package, "color": color})

    return templates.TemplateResponse(
        request=request,
        name="fragments/package_list.html",
        context={"package_data": package_data},
    )


@router.post("/package-list", response_class=HTMLResponse)
async def create_package(
    request: Request,
    package_name: Annotated[str, Form()],
    url: Annotated[str, Header(alias="HX-Current-URL")],
) -> HTMLResponse:
    logger.info(f"Attempting to add package: {package_name}")
    package_name = package_name.strip()
    query_params = parse_query_params(url)

    if package_name in query_params.packages:
        logger.warning(f"Duplicate package attempt: {package_name}")
        return HTMLResponse(
            status_code=409, content=f"'{package_name}' already selected"
        )

    if not validate_package(package_name):
        logger.error(f"Invalid package name: {package_name} - not found on PyPI")
        return HTMLResponse(
            status_code=422, content=f"'{package_name}' not found on PyPI"
        )

    query_params.packages.append(package_name)
    num_of_packages = len(query_params.packages)
    logger.info(
        f"Successfully added package: {package_name}. Total packages: {num_of_packages}"
    )

    return templates.TemplateResponse(
        request=request,
        name="fragments/package_line_item.html",
        context={
            "package_name": package_name,
            "color": generate_altair_colors(num_of_packages)[-1],
        },
        headers={"HX-Push-Url": generate_hx_push_url(query_params)},
    )


@router.delete("/package-list", response_class=HTMLResponse)
async def delete_package(
    request: Request,
    package_name: str,
    url: Annotated[str, Header(alias="HX-Current-URL")],
) -> HTMLResponse:
    logger.info(f"Attempting to delete package: {package_name}")
    package_name = package_name.strip()
    query_params = parse_query_params(url)

    try:
        query_params.packages.remove(package_name)
        logger.info(f"Successfully removed package: {package_name}")
    except ValueError:
        logger.error(f"Failed to remove package {package_name} - not found in list")
        raise

    colors = generate_altair_colors(len(query_params.packages))

    package_data = [
        {"name": package, "color": color}
        for package, color in zip(query_params.packages, colors)
    ]

    return templates.TemplateResponse(
        request=request,
        name="fragments/package_list.html",
        context={"package_data": package_data},
        headers={"HX-Push-Url": generate_hx_push_url(query_params)},
    )


@router.get("/packages-graph", response_class=HTMLResponse)
async def get_graph(
    request: Request,
    url: Annotated[str, Header(alias="HX-Current-URL")],
    time_range: TimeRangeValidValues | None = None,
) -> HTMLResponse:
    query_params = parse_query_params(url)
    theme = request.cookies.get("theme", "light")
    chart_html = ""

    if time_range is not None:
        query_params.time_range.value = time_range

    if query_params.packages:
        chart_html = generate_chart(query_params, theme).to_html()

    return templates.TemplateResponse(
        request=request,
        name="fragments/chart.html",
        context={
            "chart": chart_html,
            "query_params": query_params,
        },
        headers={"HX-Push-Url": generate_hx_push_url(query_params)},
    )
