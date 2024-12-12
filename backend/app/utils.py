from datetime import datetime, timedelta
from typing import cast
from urllib.parse import parse_qs, urlencode, urlparse

from sqlalchemy import text

from app.core.db import read_engine
from app.core.logger import logger
from app.models import QueryParams, TimeRange, TimeRangeValidValues


def start_of_week(date: str | datetime) -> str:
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")
    start = date - timedelta(days=date.weekday())
    return start.strftime("%Y-%m-%d")


def validate_package(package_name: str) -> bool:
    with read_engine.connect() as conn:
        result = conn.execute(
            text("""
            select
                package_name
            from
                pypi_packages
            where
                package_name = :package_name
            """),
            {"package_name": package_name},
        )
    exists = result.scalar() is not None
    if not exists:
        logger.info(f"Package validation failed for: {package_name}")
    return exists


def parse_query_params(url: str) -> QueryParams:
    qs = parse_qs(urlparse(url).query)
    packages = qs.get("packages", [])
    time_range = TimeRange(
        value=cast(TimeRangeValidValues, qs.get("time_range", ["3months"])[0])
    )
    return QueryParams(time_range=time_range, packages=packages)


def generate_hx_push_url(query_params: QueryParams) -> str:
    if not query_params.packages:
        return "/"
    return "?" + urlencode(
        dict(
            packages=[package for package in query_params.packages],
            time_range=query_params.time_range.value,
        ),
        doseq=True,
    )
