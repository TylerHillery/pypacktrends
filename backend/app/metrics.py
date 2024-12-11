import asyncio
from pathlib import Path

from prometheus_client import Gauge, start_http_server
from sqlalchemy import text

from app.core.config import settings
from app.core.db import read_engine
from app.core.logger import logger

SQLITE_DB_SIZE = Gauge("sqlite_database_size_bytes", "Size of SQLite database in bytes")
SQLITE_TABLE_ROWS = Gauge(
    "sqlite_table_rows", "Number of rows in table", ["table_name"]
)
SQLITE_PAGE_COUNT = Gauge("sqlite_page_count", "Number of pages in the database")
SQLITE_PAGE_SIZE = Gauge("sqlite_page_size_bytes", "Size of each page in bytes")
SQLITE_WAL_SIZE = Gauge("sqlite_wal_size_bytes", "Size of WAL file in bytes")


async def collect_metrics() -> None:
    try:
        db_path = Path(settings.SQLITE_DB_PATH)
        SQLITE_DB_SIZE.set(db_path.stat().st_size)

        wal_path = db_path.with_suffix(db_path.suffix + "-wal")
        if wal_path.exists():
            SQLITE_WAL_SIZE.set(wal_path.stat().st_size)
        else:
            SQLITE_WAL_SIZE.set(0)

        with read_engine.connect() as conn:
            page_size = conn.execute(text("PRAGMA page_size")).scalar()
            SQLITE_PAGE_SIZE.set(page_size)

            page_count = conn.execute(text("PRAGMA page_count")).scalar()
            SQLITE_PAGE_COUNT.set(page_count)

            tables = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
            for table, *_ in tables:
                row_count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                SQLITE_TABLE_ROWS.labels(table_name=table).set(row_count)

    except Exception as e:
        logger.error(f"Error collecting SQLite metrics: {str(e)}")


async def metrics_collection_task() -> None:
    while True:
        await collect_metrics()
        await asyncio.sleep(3600)


def start_metrics_server() -> None:
    try:
        start_http_server(8081)
        logger.info("Started metrics server on port 8081")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {str(e)}")
