import sys
from datetime import datetime, timedelta
from typing import Literal, cast
from urllib.parse import parse_qs, urlencode, urlparse

from pydantic import ValidationError
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
    try:
        qs = parse_qs(urlparse(url).query)
        packages = qs.get("packages", [])
        time_range = TimeRange(
            value=cast(TimeRangeValidValues, qs.get("time_range", ["3months"])[0])
        )
        show_percentage = cast(Literal["on"], qs.get("show_percentage", [None])[0])
        return QueryParams(
            time_range=time_range, packages=packages, show_percentage=show_percentage
        )
    except ValidationError as e:
        return QueryParams(error=str(e))


def generate_hx_push_url(query_params: QueryParams) -> str:
    if not query_params.packages:
        return "/"
    params = {
        "packages": [package for package in query_params.packages],
        "time_range": query_params.time_range.value,
    }
    if query_params.show_percentage is not None:
        params["show_percentage"] = [query_params.show_percentage]
    return "?" + urlencode(params, doseq=True)


def extract_last_script_tag(html_content: str) -> str | None:
    pos = len(html_content)
    while True:
        pos = html_content.rfind("<script", 0, pos)
        if pos == -1:
            return None

        end_pos = html_content.find("</script>", pos)
        if end_pos != -1:
            return html_content[pos : end_pos + len("</script>")]


def validate_date(date_text: str) -> bool:
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def parse_dates(dates: tuple[str, str]) -> tuple[str, str]:
    start_date, end_date = dates[0], dates[1]

    if not all(validate_date(date) for date in (start_date, end_date)):
        logger.error("Start date and end date must be in YYYY-MM-DD format")
        sys.exit(1)

    if end_date < start_date:
        logger.error("End date must be greater than or equal to the start date")
        sys.exit(1)

    return start_date, end_date
