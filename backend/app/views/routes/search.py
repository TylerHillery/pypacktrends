from typing import Annotated
from urllib.parse import urlparse, parse_qs

from fastapi import APIRouter, Request, Header
from fastapi.responses import HTMLResponse

from sqlalchemy import text

from app.core.config import templates
from app.core.db import read_engine

router = APIRouter()


@router.get("/search-results", response_class=HTMLResponse)
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
        "pages/search_results.html",
        {"request": request, "packages": packages, "package_name": package_name},
    )
