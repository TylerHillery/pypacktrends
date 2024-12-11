import colorsys
import random
from datetime import datetime, timedelta
from typing import cast
from urllib.parse import parse_qs, urlencode, urlparse
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
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


def generate_altair_colors(n: int, seed: int = 42) -> list[str]:
    random.seed(seed)
    colors: list[str] = []

    while len(colors) < n:
        # Python blue, yellow, green
        if len(colors) == 0:
            colors.append("#346f9e")
            continue
        elif len(colors) == 1:
            colors.append("#ffde56")
            continue
        elif len(colors) == 2:
            colors.append("#2e7d32")
            continue

        h = random.uniform(0, 1)
        s = random.uniform(0.5, 0.9)
        v = random.uniform(0.6, 0.9)
        rgb = colorsys.hsv_to_rgb(h, s, v)
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
        )
        if hex_color not in colors:
            colors.append(hex_color)

    return colors


def generate_chart(query_params: QueryParams, theme: str) -> alt.Chart:
    start_week = start_of_week(query_params.time_range.date_str)
    end_week = start_of_week(datetime.now(ZoneInfo("UTC")))
    logger.info(
        f"Generating chart for packages: {query_params.packages}, "
        f"time range: {query_params.time_range.value}, theme: {theme}, "
        f"date range: {start_week} to {end_week}"
    )
    packages = {str(i): package for i, package in enumerate(query_params.packages)}
    placeholders = ", ".join(f":{i}" for i in range(len(query_params.packages)))
    theme_config = {
        "light": {"theme": "default", "tooltip": "dark"},
        "dark": {"theme": "dark", "tooltip": "white"},
    }
    alt.theme.enable(theme_config[theme]["theme"])
    alt.ViewBackground(fillOpacity=0)

    with read_engine.connect() as conn:
        result = conn.execute(
            text(f"""
            select
                package_name,
                package_downloaded_week,
                downloads,
                cumulative_downloads,
                weeks_since_first_distribution
            from
                pypi_package_downloads_weekly_metrics
            where true
                and package_name in ({placeholders})
                and package_downloaded_week >= :start_week
                and package_downloaded_week <  :end_week
            """),
            {**packages, "start_week": start_week, "end_week": end_week},
        )
        downloads = result.fetchall()

    df = pd.DataFrame(
        downloads,
        columns=[
            "package",
            "week",
            "downloads",
            "cumulative_downloads",
            "weeks_since_first_distribution",
        ],
    )
    df["week"] = pd.to_datetime(df["week"])

    highlight = alt.selection_point(on="pointerover", fields=["package"], nearest=True)

    if query_params.time_range.value == "allTimeCumulativeAlignTimeline":
        x = dict(
            shorthand="weeks_since_first_distribution:Q",
            title="Weeks Since First Release",
            format=",",
        )
    else:
        x = dict(
            shorthand="week:T",
            title="",
            format="%Y-%m-%d",
        )

    if query_params.time_range.value in (
        "allTimeCumulative",
        "allTimeCumulativeAlignTimeline",
    ):
        y = dict(
            shorthand="cumulative_downloads:Q",
            title="Cumulative Downloads",
        )
    else:
        y = dict(
            shorthand="downloads:Q",
            title="Downloads",
        )

    base = alt.Chart(df).encode(
        x=alt.X(
            x["shorthand"],
            title=x["title"],
            axis=alt.Axis(tickCount=2.5, labelFontSize=14),
        ),
        y=alt.Y(
            y["shorthand"],
            title=y["title"],
            axis=alt.Axis(tickCount=3, labelFontSize=14),
        ),
        color="package:N",
        tooltip=[
            alt.Tooltip("package:N"),
            alt.Tooltip(**x),
            alt.Tooltip(**y, format=","),
        ],
    )

    points = base.mark_circle().encode(opacity=alt.value(0)).add_params(highlight)

    lines = base.mark_line(
        interpolate="natural", strokeWidth=4, strokeCap="round"
    ).encode(
        size=alt.when(~highlight).then(alt.value(2)).otherwise(alt.value(3)),
        color=alt.Color(
            "package:N",
            scale=alt.Scale(
                domain=packages.values(),
                range=generate_altair_colors(len(packages)),
            ),
        ).legend(orient="right", titleFontSize=16, labelFontSize=14),
    )

    return (
        (points + lines)
        .properties(
            width="container",
            height=400,
            usermeta={
                "embedOptions": {
                    "tooltip": {"theme": theme_config[theme]["tooltip"]},
                    "actions": False,
                },
            },
        )
        .configure(background="rgba(0,0,0,0)")
    )
