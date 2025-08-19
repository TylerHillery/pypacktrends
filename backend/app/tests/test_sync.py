from sqlalchemy import Engine, text

from app.sync import sync_pypi_downloads, sync_pypi_packages


def test_sync_pypi_packages(read_engine: Engine, write_engine: Engine) -> None:
    limit_value = 10
    sync_pypi_packages(read_engine, write_engine, limit_value)
    with read_engine.connect() as conn:
        result = conn.execute(text("select count(*) from pypi_packages"))
        num_of_rows_inserted = result.scalar()
    assert num_of_rows_inserted == limit_value


def test_sync_pypi_downloads(read_engine: Engine, write_engine: Engine) -> None:
    limit_value = 8
    start_date = "2024-11-23"
    end_date = "2024-11-23"
    sync_pypi_downloads(write_engine, start_date, end_date, limit_value)
    with read_engine.connect() as conn:
        result = conn.execute(
            text("select count(*) from pypi_package_downloads_weekly_metrics")
        )
        num_of_rows_inserted = result.scalar()
    assert num_of_rows_inserted == limit_value
