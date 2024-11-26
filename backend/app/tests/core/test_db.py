from sqlalchemy import Engine, text
from sqlalchemy.engine.url import make_url

from app.core.config import settings
from app.tests.conftest import SQLITE_TEST_DB


def test_db_manager_pragma_fk(read_engine: Engine) -> None:
    with read_engine.connect() as conn:
        result = conn.execute(text("pragma foreign_keys;")).scalar()
        expected_result = 1
        assert result == expected_result


def test_db_manager_pragma_busy_timeout(read_engine: Engine) -> None:
    with read_engine.connect() as conn:
        result = conn.execute(text("pragma busy_timeout;")).scalar()
        expected_result = 5000
        assert result == expected_result


def test_db_manager_pragma_journal_mode(read_engine: Engine) -> None:
    with read_engine.connect() as conn:
        result = conn.execute(text("pragma journal_mode;")).scalar()
        expected_result = "wal"
        assert result == expected_result


def test_db_manager_pragma_synchronous(read_engine: Engine) -> None:
    with read_engine.connect() as conn:
        result = conn.execute(text("pragma synchronous;")).scalar()
        expected_result = 1  # normal
        assert result == expected_result


def test_db_manager_url_read_engine(read_engine: Engine) -> None:
    result = read_engine.url
    expected_result = make_url(f"{settings.SQLALCHEMY_DATABASE_URI}&mode=ro")
    assert result == expected_result
    assert result.database.removeprefix("file:") == str(SQLITE_TEST_DB)


def test_db_manager_url_write_engine(write_engine: Engine) -> None:
    result = write_engine.url
    expected_result = make_url(settings.SQLALCHEMY_DATABASE_URI)
    assert result == expected_result
    assert result.database.removeprefix("file:") == str(SQLITE_TEST_DB)
