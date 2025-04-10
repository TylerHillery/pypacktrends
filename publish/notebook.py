import os

import altair as alt
from dotenv import load_dotenv
from pyiceberg.catalog.rest import RestCatalog

load_dotenv()

WAREHOUSE = os.getenv("WAREHOUSE")
TOKEN = os.getenv("TOKEN")
CATALOG_URI = os.getenv("CATALOG_URI")

catalog = RestCatalog(
    name="pypacktrends",
    warehouse=WAREHOUSE,
    uri=CATALOG_URI,
    token=TOKEN,
)

catalog.list_tables("default")

table = catalog.load_table("default.pypi_package_downloads_per_week")

con = table.scan().to_duckdb("pypi_package_downloads_per_week")

top_10_packages_by_downloads_last_month = con.query("""
select
    date_trunc('month', package_downloaded_week) as package_downloaded_month,
    package_name,
    sum(downloads) as downloads
from
    pypi_package_downloads_per_week
group by
    all
order by
    1 desc,
    3 desc
limit
    10
""")

top_10_packages_by_downloads_last_month.show()

chart = (
    alt.Chart(top_10_packages_by_downloads_last_month.to_df())
    .mark_bar()
    .encode(
        y=alt.Y("package_name:N", sort="-x", title="Package Name"),
        x=alt.X("downloads:Q", title="Downloads"),
        tooltip=["package_name", "downloads"],
    )
    .properties(title="Top 10 PyPI Packages by Downloads", width=600, height=400)
)

chart
