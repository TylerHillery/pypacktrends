from typing import Annotated, Literal

from fastapi import APIRouter, Form, Header, Request
from fastapi.responses import HTMLResponse

from app.chart import generate_altair_colors, generate_chart
from app.core.logger import logger
from app.core.templates import templates
from app.models import TimeRangeValidValues
from app.utils import (
    extract_last_script_tag,
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

    if query_params.error:
        logger.warning(query_params.error)
        return HTMLResponse(status_code=422, content=query_params.error)

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
    package_name = package_name.strip().lower()
    query_params = parse_query_params(url)

    if query_params.error:
        logger.warning(query_params.error)
        return HTMLResponse(status_code=422, content=query_params.error)

    if package_name in query_params.packages:
        logger.warning(f"Duplicate package attempt: {package_name}")
        return HTMLResponse(
            status_code=409, content=f"'{package_name}' already selected"
        )

    if not validate_package(package_name):
        logger.warning(f"Invalid package name: {package_name} - not found on PyPI")
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
    package_name = package_name.strip().lower()
    query_params = parse_query_params(url)

    if query_params.error:
        logger.warning(query_params.error)
        return HTMLResponse(status_code=422, content=query_params.error)

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
    show_percentage: Literal["on"] | None = None,
) -> HTMLResponse:
    query_params = parse_query_params(url)

    if query_params.error:
        logger.warning(query_params.error)
        return HTMLResponse(status_code=422, content=query_params.error)

    theme = request.cookies.get("theme", "light")
    chart_html = ""
    last_script_tag = ""

    if time_range is not None:
        query_params.time_range.value = time_range

    if (
        show_percentage is not None
        or request.headers["HX-Trigger"] == "show-percentage"
    ):
        query_params.show_percentage = show_percentage

    if query_params.packages:
        chart_html = generate_chart(query_params, theme).to_html(fullhtml=False)
        last_script_tag = extract_last_script_tag(chart_html) or ""

    headers = {}

    if request.headers["HX-Trigger"] in ["time-range", "show-percentage"]:
        headers["HX-Push-Url"] = generate_hx_push_url(query_params)

    return templates.TemplateResponse(
        request=request,
        name="fragments/chart.html",
        context={
            "chart": last_script_tag,
            "query_params": query_params,
        },
        headers=headers,
    )


@router.get("/embed", response_class=HTMLResponse)
async def get_embed(
    request: Request,
    time_range: TimeRangeValidValues | None = None,
    theme: Literal["light", "dark"] | None = None,
    show_percentage: Literal["on"] | None = None,
) -> HTMLResponse:
    """Endpoint for embedded charts that can be used in iframes."""
    query_params = parse_query_params(str(request.url))

    if query_params.error:
        logger.warning(query_params.error)
        return HTMLResponse(status_code=422, content=query_params.error)

    if not theme:
        theme = request.cookies.get("theme", "light")

    if time_range is not None:
        query_params.time_range.value = time_range

    if show_percentage is not None:
        query_params.show_percentage = show_percentage

    if not query_params.packages:
        return HTMLResponse(content="No packages selected")

    chart_html = generate_chart(query_params, theme).to_html(fullhtml=True)

    attribution_style = """
        <style>
            .pypacktrends-attribution {
                text-align: center;
                padding: 8px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 12px;
            }
            .pypacktrends-attribution a {
                color: #666;
                text-decoration: none;
            }
            .pypacktrends-attribution a:hover {
                text-decoration: underline;
            }
        </style>
    """

    attribution_html = f"""
        <div class="pypacktrends-attribution">
            <a href="{str(request.url).replace('/embed', '')}" target="_blank">
                View on pypacktrends.com
            </a>
        </div>
    """

    modified_html = chart_html.replace(
        "<body>", f"<body>{attribution_style}{attribution_html}"
    )

    return HTMLResponse(content=modified_html)
