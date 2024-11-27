import pytest
from sqlalchemy import Engine, text

from app.sync import parse_dates, sync_pypi_downloads, sync_pypi_packages, validate_date


def test_validate_date_true() -> None:
    result = validate_date("2024-10-14")
    expected_result = True
    assert result == expected_result


def test_validate_date_false() -> None:
    result = validate_date("2024-15-55")
    expected_result = False
    assert result == expected_result


def test_parse_dates_args_length() -> None:
    with pytest.raises(SystemExit):
        parse_dates(["sync.py", "packages"])


def test_parse_dates_invalid_format() -> None:
    with pytest.raises(SystemExit):
        parse_dates(["sync.py", "packages", "2024-10-01", "not-a-date"])


def test_parse_dates_end_date_gt_start_date() -> None:
    with pytest.raises(SystemExit):
        parse_dates(["sync.py", "packages", "2024-12-01", "2024-01-01"])


def test_parse_dates_valid_format() -> None:
    result = parse_dates(["sync.py", "packages", "2024-10-01", "2024-12-01"])
    expected_result = ("2024-10-01", "2024-12-01")
    assert result == expected_result


def test_sync_main_args_length() -> None:
    with pytest.raises(SystemExit):
        parse_dates(["sync.py"])


def test_sync_main_invalid_entity() -> None:
    with pytest.raises(SystemExit):
        parse_dates(["sync.py", "pack"])


def test_sync_pypi_packages(read_engine: Engine, write_engine: Engine) -> None:
    limit_value = 10
    sync_pypi_packages(read_engine, write_engine, limit_value)
    with read_engine.connect() as conn:
        result = conn.execute(text("select count(*) from pypi_packages"))
        num_of_rows_inserted = result.scalar()
    assert num_of_rows_inserted == limit_value


def test_sync_pypi_downloads(read_engine: Engine, write_engine: Engine) -> None:
    limit_value = 10
    start_date = "2024-11-23"
    end_date = "2024-11-23"
    sync_pypi_downloads(write_engine, start_date, end_date, limit_value)
    with read_engine.connect() as conn:
        result = conn.execute(
            text("select count(*) from pypi_package_downloads_per_day")
        )
        num_of_rows_inserted = result.scalar()
    assert num_of_rows_inserted == limit_value
