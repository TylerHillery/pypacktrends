from typing import Annotated

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from sqlalchemy import text

from app.core.config import templates
from app.core.db import read_engine

router = APIRouter()


@router.post("/search", response_class=HTMLResponse)
def search(request: Request, package_name: Annotated[str, Form()]):
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
        "home/search.html",
        {"request": request, "packages": packages, "package_name": package_name},
    )
