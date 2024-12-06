from pathlib import Path
from unittest import mock

import pytest
from sqlalchemy import Engine, text

from app.alembic.utils import (
    NullLogger,
    get_sql_migration_file,
    read_sql_file,
    run_sql_statements,
)


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).parents[3]


@pytest.fixture
def alembic_migration_file(project_root: Path) -> Path:
    return project_root / "app/alembic/versions/eb3ad385519a_init_database.py"


@pytest.fixture
def alembic_sql_upgrade_file(project_root: Path) -> Path:
    return project_root / "app/alembic/versions/eb3ad385519a_init_database_upgrade.sql"


@pytest.fixture
def alembic_sql_downgrade_file(project_root: Path) -> Path:
    return (
        project_root / "app/alembic/versions/eb3ad385519a_init_database_downgrade.sql"
    )


def test_read_sql_file_missing() -> None:
    with pytest.raises(FileNotFoundError):
        read_sql_file(Path("/tmp/file.sql"))


def test_read_sql_file(alembic_sql_upgrade_file: Path) -> None:
    def normalize_whitespace(sql: str) -> str:
        return " ".join(sql.split())

    result = tuple(
        normalize_whitespace(stmt) for stmt in read_sql_file(alembic_sql_upgrade_file)
    )
    expected_result = tuple(
        normalize_whitespace(stmt)
        for stmt in (
            "pragma journal_mode = wal",
            """create table pypi_package_downloads_weekly_metrics (
                package_name                    text    not null,
                package_downloaded_week         text    not null,
                downloads                       integer not null,
                cumulative_downloads            integer not null,
                first_distribution_week         text    not null,
                weeks_since_first_distribution  integer not null,
                synced_at                       text    not null,
                primary key (package_name, package_downloaded_week)
            ) strict
            """,
            """create index idx_package_name
               on pypi_package_downloads_weekly_metrics (package_name)
            """,
            """create index idx_package_downloaded_week
               on pypi_package_downloads_weekly_metrics (package_downloaded_week)
            """,
            """create table pypi_packages (
                package_name            text not null primary key,
                latest_package_version  text not null,
                package_summary         text,
                package_home_page       text,
                package_download_url    text,
                package_uploaded_at     text not null,
                synced_at               text not null
            ) strict
            """,
            """create index idx_package_uploaded_at
               on pypi_packages (package_uploaded_at)
            """,
        )
    )
    assert result == expected_result


def test_get_sql_file_name_upgrade(
    alembic_migration_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_stack = [
        mock.Mock(),
        mock.Mock(filename=str(alembic_migration_file), function="upgrade"),
    ]
    monkeypatch.setattr("inspect.stack", lambda: mock_stack)
    result = get_sql_migration_file()
    excepted_result = (
        alembic_migration_file.parent / f"{alembic_migration_file.stem}_upgrade.sql"
    )
    assert result == excepted_result


def test_get_sql_file_name_downgrade(
    alembic_migration_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_stack = [
        mock.Mock(),
        mock.Mock(filename=str(alembic_migration_file), function="downgrade"),
    ]
    monkeypatch.setattr("inspect.stack", lambda: mock_stack)
    result = get_sql_migration_file()
    excepted_result = (
        alembic_migration_file.parent / f"{alembic_migration_file.stem}_downgrade.sql"
    )
    assert result == excepted_result


def test_get_sql_file_name_invalid(
    alembic_migration_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_stack = [
        mock.Mock(),
        mock.Mock(filename=str(alembic_migration_file), function="invalid"),
    ]
    monkeypatch.setattr("inspect.stack", lambda: mock_stack)
    with pytest.raises(
        ValueError,
        match="Function 'invalid' is not a valid Alembic migration function. Expected 'upgrade' or 'downgrade'.",
    ):
        get_sql_migration_file()


def test_run_sql_statements(
    write_engine: Engine, read_engine: Engine, tmp_path: Path
) -> None:
    sql_file = tmp_path / "test_statements.sql"
    sql_file.write_text(
        """
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        INSERT INTO test_table (id, name) VALUES (1, 'test_name');
        """
    )

    executed_statements = run_sql_statements(write_engine, sql_file, NullLogger())

    assert len(executed_statements) == 2
    assert executed_statements[0].startswith("CREATE TABLE test_table")
    assert executed_statements[1].startswith("INSERT INTO test_table")

    with read_engine.connect() as conn:
        result = conn.execute(text("SELECT id, name FROM test_table")).fetchall()

    assert result == [(1, "test_name")]


def test_run_sql_statements_error(write_engine: Engine, tmp_path: Path) -> None:
    sql_file = tmp_path / "test_invalid_statements.sql"
    sql_file.write_text("INSERT INTO non_existent_table (id) VALUES (1);")

    with pytest.raises(Exception):
        run_sql_statements(write_engine, sql_file, logger=NullLogger())
