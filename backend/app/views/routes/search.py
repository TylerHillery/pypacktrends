from typing import Annotated
from fastapi import APIRouter, Request, Header
from fastapi.responses import HTMLResponse

from sqlalchemy import text

from app.core.config import templates
from app.core.db import read_engine
from app.utils import parse_url_params, validate_package

router = APIRouter()


@router.get("/package-search-input", response_class=HTMLResponse)
def get_search_input(
    request: Request,
    package_name: str,
    hx_current_url: Annotated[str, Header(alias="HX-Current-URL")] = None,
):
    package_name = package_name.strip()
    is_valid_submission = True
    error_message = ""
    current_packages, _ = parse_url_params(hx_current_url)

    if package_name != "":
        if package_name in current_packages: 
            is_valid_submission = False
            error_message = f"'{package_name}' already selected"
        elif not validate_package(package_name):
            is_valid_submission = False
            error_message = f"'{package_name}' not found on PyPI"

    return templates.TemplateResponse(
        request=request,
        name="fragments/package_search_input.html",
        context={
            "package_name": package_name,
            "is_valid_submission": is_valid_submission,
            "error_message": error_message
        },
    )


@router.get("/package-search-results", response_class=HTMLResponse)
def get_search_results(
    request: Request,
    package_name: str,
):
    with read_engine.connect() as conn:
        result = conn.execute(
            text("""
            select
                 package_name,
                 package_summary
            from
                pypi_packages
            where
                lower(package_name) like :package_name
            order by
                lower(package_name) limit 10
            """),
            {"package_name": package_name + "%"},
        )
        packages = result.fetchall()

    return templates.TemplateResponse(
        "pages/package_search_results.html",
        {"request": request, "packages": packages, "package_name": package_name},
    )
