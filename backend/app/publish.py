import os
import sys
import time

import duckdb
from duckdb import DuckDBPyConnection
from google.cloud import bigquery

from app.core.config import settings
from app.core.logger import logger
from app.utils import parse_dates


class DuckDBClient:
    def __init__(
        self,
        gcp_project: str,
        r2_access_key_id: str,
        r2_secret_access_key: str,
        r2_account_id: str,
        r2_bucket_name: str,
        r2_custom_domain: str,
    ):
        self.gcp_project = gcp_project
        self.r2_access_key_id = r2_access_key_id
        self.r2_secret_access_key = r2_secret_access_key
        self.r2_account_id = r2_account_id
        self.r2_bucket_path = f"r2://{r2_bucket_name}"
        self.r2_custom_domain = r2_custom_domain
        self.conn = self._init_duckdb_client()

    def _init_duckdb_client(self) -> DuckDBPyConnection:
        conn = duckdb.connect("/tmp/duckdb_github_actions.db")
        sql = f"""
CREATE SECRET (
    TYPE r2,
    KEY_ID '{self.r2_access_key_id}',
    SECRET '{self.r2_secret_access_key}',
    ACCOUNT_ID '{self.r2_account_id}'
);

CREATE OR REPLACE TABLE pypi_downloads (
    package_name VARCHAR,
    package_downloaded_week DATE,
    downloads BIGINT,
    cumulative_downloads BIGINT,
    first_distribution_week DATE,
    weeks_since_first_distribution INTEGER,
    published_at TIMESTAMP,
    week DATE
);
"""
        conn.execute(sql)
        logger.info("DuckDB client initialized")
        return conn


def publish_pypi_downloads_manifest(duckdb_client: DuckDBClient) -> None:
    export_path = f"{duckdb_client.r2_bucket_path}/pypi-weekly-downloads"
    manifest_path = f"{export_path}/manifest.parquet"

    sql = f"""
CREATE TABLE pypi_downloads_manifest AS
with urls as (
    select distinct
        regexp_extract(filename, 'package_downloaded_week=([0-9\\-]+)', 1) AS package_downloaded_week,
        replace(
            replace(filename, '{duckdb_client.r2_bucket_path}', '{duckdb_client.r2_custom_domain}'),
            '=',
            '%3D'
        ) as url
    from
        read_parquet('{export_path}/*/*.parquet')
)

select * from urls order by 1;

COPY pypi_downloads_manifest TO '{manifest_path}'
(FORMAT parquet, OVERWRITE_OR_IGNORE);
"""
    duckdb_client.conn.execute(sql)
    logger.info(f"Manifest updated: {manifest_path}")


def publish_pypi_downloads(
    duckdb_client: DuckDBClient, start_date: str, end_date: str
) -> None:
    export_path = f"{duckdb_client.r2_bucket_path}/pypi-weekly-downloads/"

    client = bigquery.Client()

    select_query = f"""
SELECT
    package_name,
    package_downloaded_week,
    downloads,
    cumulative_downloads,
    first_distribution_week,
    weeks_since_first_distribution,
    current_datetime('UTC') as published_at,
    package_downloaded_week as week
FROM
    `{duckdb_client.gcp_project}.dbt.pypi_package_downloads_weekly_metrics`
WHERE
    package_downloaded_week BETWEEN '{start_date}' AND '{end_date}'
ORDER BY
    package_downloaded_week,
    package_name
"""

    logger.info(f"Query most recent distributions: {select_query}")

    job_config = bigquery.QueryJobConfig(
        labels={
            "application": "pypacktrends",
            "component": "publish",
            "type": "downloads",
            "environment": settings.ENVIRONMENT,
        }
    )
    rows = client.query(select_query, job_config=job_config).result()
    total_rows = rows.total_rows

    if total_rows < 1:
        logger.info("No rows to insert")
        return

    logger.info(f"Total rows to insert: {total_rows}")

    upsert_sql = """
    INSERT INTO pypi_downloads
        (package_name, package_downloaded_week, downloads, cumulative_downloads, first_distribution_week, weeks_since_first_distribution, published_at, week)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    start_time = time.time()
    row_count = 0
    batch_count = 0
    for page in rows.pages:
        batch_count += 1
        start_batch_time = time.time()

        downloads = [
            (
                row["package_name"],
                row["package_downloaded_week"],
                row["downloads"],
                row["cumulative_downloads"],
                row["first_distribution_week"],
                row["weeks_since_first_distribution"],
                row["published_at"],
                row["week"],
            )
            for row in page
        ]

        row_count += len(downloads)

        logger.info(f"Inserting {row_count} of {total_rows} rows...")

        duckdb_client.conn.executemany(upsert_sql, downloads)

        batch_time = time.time() - start_batch_time
        logger.info(f"Batch {batch_count} inserted in {batch_time:.2f} seconds.")

    export_sql = f"""
COPY pypi_downloads TO '{export_path}'
(FORMAT parquet, PARTITION_BY (week), OVERWRITE_OR_IGNORE);
"""

    duckdb_client.conn.execute(export_sql)
    total_time = time.time() - start_time
    logger.info(
        f"Successfully exported PyPI weekly downloads from {start_date} to {end_date} to R2 bucket path: {export_path} in {total_time:.2f} seconds."
    )


def main() -> None:
    if len(sys.argv) != 3:
        logger.error("Usage: python publish.py <start_date> <end_date>")
        sys.exit(1)

    _, start_date, end_date = sys.argv

    gcp_project = os.getenv("GCP_PROJECT")

    if gcp_project is None:
        raise ValueError("GCP_PROJECT environment variable is not set")

    cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    if cloudflare_account_id is None:
        raise ValueError("CLOUDFLARE_ACCOUNT_ID environment variable is not set")

    r2_access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
    if r2_access_key_id is None:
        raise ValueError("CLOUDFLARE_R2_ACCESS_KEY_ID environment variable is not set")

    r2_secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
    if r2_secret_access_key is None:
        raise ValueError(
            "CLOUDFLARE_R2_SECRET_ACCESS_KEY environment variable is not set"
        )

    r2_bucket_name = os.getenv("CLOUDFLARE_R2_PUBLIC_BUCKET_NAME")
    if r2_bucket_name is None:
        raise ValueError(
            "CLOUDFLARE_R2_PUBLIC_BUCKET_NAME environment variable is not set"
        )

    r2_custom_domain = os.getenv("CLOUDFLARE_R2_CUSTOM_DOMAIN")
    if r2_custom_domain is None:
        raise ValueError("CLOUDFLARE_R2_CUSTOM_DOMAIN environment variable is not set")

    duckdb_client = DuckDBClient(
        gcp_project=gcp_project,
        r2_access_key_id=r2_access_key_id,
        r2_secret_access_key=r2_secret_access_key,
        r2_account_id=cloudflare_account_id,
        r2_bucket_name=r2_bucket_name,
        r2_custom_domain=r2_custom_domain,
    )

    publish_pypi_downloads(duckdb_client, *parse_dates((start_date, end_date)))
    publish_pypi_downloads_manifest(duckdb_client)


if __name__ == "__main__":
    main()
