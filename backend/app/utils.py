from datetime import date, timedelta
import random
import colorsys
from urllib.parse import urlparse, parse_qs, urlencode
from sqlalchemy import text
import altair as alt
import pandas as pd

from app.core.db import read_engine

DATE_FORMAT: str = "%Y-%m-%d"


def get_date_n_days_ago(date: date, n_days: int) -> str:
    return (date - timedelta(days=n_days)).strftime(DATE_FORMAT)


def parse_packages(hx_current_url: str) -> list[str]:
    return parse_qs(urlparse(hx_current_url).query).get("packages", [])


def generate_push_url(packages: list[str]) -> str:
    return f"?{urlencode({'packages': packages}, doseq=True)}" if packages else "/"


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
    return result.scalar() is not None


def generate_altair_colors(n: int, seed: int = 42) -> list[str]:
    if n < 1:
        raise ValueError("n must be at least 1")

    random.seed(seed)
    colors = []

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


def generate_chart(packages: list[str]) -> alt.Chart:
    packages = {str(i): package for i, package in enumerate(packages)}
    placeholders = ", ".join(f":{i}" for i in range(len(packages)))

    with read_engine.connect() as conn:
        result = conn.execute(
            text(f"""
            select
                package_name,
                date(package_downloaded_date, 'weekday 0', '-6 days') as week,
                sum(downloads) as downloads
            from
                pypi_package_downloads_per_day
            where true
                and package_name in ({placeholders})
                and date(package_downloaded_date, 'weekday 0', '-6 days') != date('now', 'weekday 0', '-6 days')
            group by
                1,2
            """),
            packages,
        )
        downloads = result.fetchall()

    df = pd.DataFrame(downloads, columns=["package", "week", "downloads"])
    df["week"] = pd.to_datetime(df["week"])

    highlight = alt.selection_point(on="pointerover", fields=["package"], nearest=True)

    base = alt.Chart(df).encode(
        x=alt.X("week:T", title=None, axis=alt.Axis(tickCount=2)),
        y=alt.Y("downloads:Q", title=None, axis=alt.Axis(tickCount=4)),
        color="package:N",
        tooltip=[
            alt.Tooltip("package:N"),
            alt.Tooltip("week:T", format="%Y-%m-%d"),
            alt.Tooltip("downloads:Q", format=","),
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
        ).legend(orient="top"),
    )

    return (points + lines).properties(
        width="container",
        height=400,
        usermeta={"embedOptions": {"tooltip": {"theme": "dark"}, "actions": False}},
    )


if __name__ == "__main__":
    current_packages = {"duckdb", "polars"}
    generate_chart(current_packages).show()
