import random
import colorsys
from urllib.parse import urlparse, parse_qs, urlencode
from sqlalchemy import text
import altair as alt
import pandas as pd

from app.core.db import read_engine
from app.models import TimeRangeModel
from datetime import datetime, timedelta


def start_of_week(date: str) -> str:
    dt = datetime.strptime(date, "%Y-%m-%d")
    start = dt - timedelta(days=dt.weekday())
    return start.strftime("%Y-%m-%d")


def parse_url_params(hx_current_url: str) -> tuple[list[str], str]:
    parsed_qs = parse_qs(urlparse(hx_current_url).query)
    packages = parsed_qs.get("packages", [])
    time_range = parsed_qs.get("time_range", ["3months"])[0]
    return packages, time_range


def generate_push_url(packages: list[str], time_range: TimeRangeModel | None) -> str:
    if not packages:
        return "/"

    params = {"packages": packages, "time_range": time_range}
    return f"?{urlencode(params, doseq=True)}"


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


def generate_chart(
    packages: list[str], time_range: TimeRangeModel, theme: str | None
) -> alt.Chart:
    packages = {str(i): package for i, package in enumerate(packages)}
    placeholders = ", ".join(f":{i}" for i in range(len(packages)))
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
                and package_downloaded_week >= :week 
                and package_downloaded_week <  date('now', 'weekday 0', '-6 days')  
            """),
            {**packages, "week": start_of_week(time_range.date)},
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

    # fix tool tip cumulative downlodas
    if time_range.value == "allTimeCumulativeAlignTimeline":
        x = "weeks_since_first_distribution:Q"
        x_title = "Weeks Since First Release"
        x_format = ","
    else:
        x = "week:T"
        x_title = "Week"
        x_format = "%Y-%m-%d"

    if time_range.value in ("allTimeCumulative", "allTimeCumulativeAlignTimeline"):
        y = "cumulative_downloads:Q"
        y_title = "Cumulative Downloads"
        y_format = ","
    else:
        y = "downloads:Q"
        y_title = "Downloads"
        y_format = ","

    base = alt.Chart(df).encode(
        x=alt.X(x, title=x_title, axis=alt.Axis(tickCount=2.5, labelFontSize=14)),
        y=alt.Y(y, title=y_title, axis=alt.Axis(tickCount=3, labelFontSize=14)),
        color="package:N",
        tooltip=[
            alt.Tooltip("package:N"),
            alt.Tooltip(x, title=x_title, format=x_format),
            alt.Tooltip(y, title=y_title, format=y_format)
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


if __name__ == "__main__":
    current_packages = ["duckdb", "polars"]
    generate_chart(current_packages, TimeRangeModel(value="allTimeCumulative"), "dark").show()
