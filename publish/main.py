import os

import duckdb
from dotenv import load_dotenv
from pyiceberg.catalog.rest import RestCatalog

load_dotenv()

# Define catalog connection details (replace variables)
WAREHOUSE = os.getenv("WAREHOUSE")
TOKEN = os.getenv("TOKEN")
CATALOG_URI = os.getenv("CATALOG_URI")


def main():
    catalog = RestCatalog(
        name="pypacktrends",
        warehouse=WAREHOUSE,
        uri=CATALOG_URI,
        token=TOKEN,
    )

    con = duckdb.connect()

    load_duckdb_extensions = """
    install bigquery from community;
    load bigquery;
    attach 'project=pypacktrends-prod' AS pypacktrends_prod (type bigquery, read_only);
    """

    con.sql(load_duckdb_extensions)

    select_query = """
    select
        package_name,
        latest_package_version,
        package_summary,
        package_home_page,
        package_download_url,
    from
        pypacktrends_prod.dbt.pypi_packages
    """

    select_query = """
    select
        *
    from
        pypacktrends_prod.dbt.pypi_package_downloads_per_week
    """

    pypi_downloads = con.query(select_query).arrow()

    # table = catalog.load_table("default.pypi_downloads")

    # Create an Iceberg table
    table = catalog.create_table(
        ("default", "pypi_package_downloads_per_week"),
        schema=pypi_downloads.schema,
    )

    table.overwrite(pypi_downloads)


if __name__ == "__main__":
    main()
