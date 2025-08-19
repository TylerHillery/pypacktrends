import sys
import time

from google.cloud import bigquery
from sqlalchemy import Engine, text

from app.core.config import settings
from app.core.db import read_engine, write_engine
from app.core.logger import logger
from app.utils import parse_dates, start_of_week


def sync_pypi_packages(
    read_engine: Engine, write_engine: Engine, limit: int | None = None
) -> None:
    logger.info("Syncing PyPI packages to SQLite...")

    with read_engine.connect() as conn:
        result = conn.execute(
            text("select max(package_uploaded_at) from pypi_packages")
        )
        last_uploaded_at = result.scalar()

    client = bigquery.Client()

    select_query = f"""
    select
        package_name,
        latest_package_version,
        package_summary,
        package_home_page,
        package_download_url,
        format_timestamp("%Y-%m-%dT%H:%M:%SZ", package_uploaded_at) as package_uploaded_at,
        format_timestamp("%Y-%m-%dT%H:%M:%SZ", current_datetime("UTC")) as synced_at
    from
        pypacktrends-prod.dbt.pypi_packages
    where
        package_uploaded_at > '{last_uploaded_at or "1900-01-01T00:00:00Z"}'
    order by
        package_name
    """

    if limit is not None:
        select_query += f"limit {limit}"

    logger.info(f"Query most recent distributions: {select_query}")

    BATCH_SIZE = 5000

    job_config = bigquery.QueryJobConfig(
        labels={
            "application": "pypacktrends",
            "component": "sync",
            "type": "packages",
            "environment": settings.ENVIRONMENT,
        }
    )
    rows = client.query(select_query, job_config=job_config).result(
        page_size=BATCH_SIZE
    )
    total_rows = rows.total_rows

    if total_rows < 1:
        logger.info("No rows to insert")
        return

    logger.info(f"Total rows to insert: {total_rows}")

    upsert_sql = text("""
    insert or replace into pypi_packages
        (package_name, latest_package_version, package_summary, package_home_page, package_download_url, package_uploaded_at, synced_at)
    values
        (:package_name, :latest_package_version, :package_summary, :package_home_page, :package_download_url, :package_uploaded_at, :synced_at)
    """)

    start_time = time.time()

    with write_engine.begin() as conn:
        row_count = 0
        batch_count = 0
        for page in rows.pages:
            batch_count += 1
            start_batch_time = time.time()

            packages = [dict(row.items()) for row in page]

            row_count += len(packages)

            logger.info(f"Inserting {row_count} of {total_rows} rows...")

            conn.execute(upsert_sql, packages)

            batch_time = time.time() - start_batch_time
            logger.info(f"Batch {batch_count} inserted in {batch_time:.2f} seconds.")

    total_time = time.time() - start_time
    logger.info(f"Sync completed in {total_time:.2f} seconds.")


def sync_pypi_downloads(
    write_engine: Engine, start_date: str, end_date: str, limit: int | None = None
) -> None:
    start_week, end_week = start_of_week(start_date), start_of_week(end_date)

    logger.info(
        f"Syncing PyPI downloads to SQLite for weeks {start_week} to {end_week}"
    )

    client = bigquery.Client()

    select_query = f"""
    select
        package_name,
        package_downloaded_week,
        downloads,
        cumulative_downloads,
        first_distribution_week,
        weeks_since_first_distribution,
        format_timestamp('%Y-%m-%dT%H:%M:%SZ', current_datetime("UTC")) as synced_at
    from
        pypacktrends-prod.dbt.pypi_package_downloads_weekly_metrics
    where
        package_downloaded_week between '{start_week}' and '{end_week}'
    """

    if limit is not None:
        select_query += f"limit {limit}"

    logger.info(f"Query downloads: {select_query}")

    BATCH_SIZE = 5000
    job_config = bigquery.QueryJobConfig(
        labels={
            "application": "pypacktrends",
            "component": "sync",
            "type": "downloads",
            "environment": settings.ENVIRONMENT,
        }
    )
    rows = client.query(select_query, job_config=job_config).result(
        page_size=BATCH_SIZE
    )
    total_rows = rows.total_rows

    if total_rows < 1:
        logger.info("No rows to insert")
        return

    logger.info(f"Total rows to insert: {total_rows}")

    delete_sql = text("""
    delete from pypi_package_downloads_weekly_metrics
    where package_downloaded_week between :start_week and :end_week
    """)

    insert_sql = text("""
    insert into pypi_package_downloads_weekly_metrics (
        package_name,
        package_downloaded_week,
        downloads,
        cumulative_downloads,
        first_distribution_week,
        weeks_since_first_distribution,
        synced_at
    )
    values (
        :package_name,
        :package_downloaded_week,
        :downloads,
        :cumulative_downloads,
        :first_distribution_week,
        :weeks_since_first_distribution,
        :synced_at
    )
    """)

    start_time = time.time()

    with write_engine.begin() as conn:
        conn.execute(delete_sql, {"start_week": start_week, "end_week": end_week})
        row_count = 0
        batch_count = 0
        for page in rows.pages:
            batch_count += 1
            start_batch_time = time.time()

            packages = [dict(row.items()) for row in page]
            row_count += len(packages)

            logger.info(f"Inserting {row_count} of {total_rows} rows...")

            conn.execute(insert_sql, packages)

            batch_time = time.time() - start_batch_time
            logger.info(f"Batch {batch_count} inserted in {batch_time:.2f} seconds.")

    total_time = time.time() - start_time
    logger.info(f"Sync completed in {total_time:.2f} seconds.")


def main() -> None:
    if len(sys.argv) != 4:
        logger.error("Usage: python sync.py <entity> <start_date> <end_date>")
        sys.exit(1)

    _, entity, start_date, end_date = sys.argv

    match entity:
        case "packages":
            sync_pypi_packages(read_engine, write_engine)
        case "downloads":
            sync_pypi_downloads(write_engine, *parse_dates((start_date, end_date)))
        case "all":
            sync_pypi_packages(read_engine, write_engine)
            sync_pypi_downloads(write_engine, *parse_dates((start_date, end_date)))
        case _:
            logger.error("Unknown entity. Please use 'packages' or 'downloads'")
            sys.exit(1)


if __name__ == "__main__":
    main()
