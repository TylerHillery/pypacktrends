import os
import subprocess
from pathlib import Path
from typing import Generator
from unittest import mock

import pytest
from sqlalchemy import Engine

from app.core.config import Settings
from app.core.db import DBConnectionManager

ALEMBIC_CONFIG_PATH = Path(__file__).parent.parent.parent / "alembic.ini"
SQLITE_TEST_DB = (
    Path(__file__).parent.parent.parent.parent / "data/pypacktrends_test.db"
)


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    with mock.patch.dict(os.environ, {"SQLITE_DB_PATH": str(SQLITE_TEST_DB)}):
        test_settings = Settings()
        return test_settings


@pytest.fixture(scope="session")
def run_db_migrations() -> Generator[None, None, None]:
    with mock.patch.dict(os.environ, {"SQLITE_DB_PATH": str(SQLITE_TEST_DB)}):
        if not ALEMBIC_CONFIG_PATH.exists():
            raise FileNotFoundError(
                f"Alembic config file not found at {ALEMBIC_CONFIG_PATH}"
            )

        if SQLITE_TEST_DB.exists():
            SQLITE_TEST_DB.unlink()

        subprocess.run(
            ["alembic", "-c", str(ALEMBIC_CONFIG_PATH), "upgrade", "head"], check=True
        )

        yield


@pytest.fixture(scope="session")
def db_manager(run_db_migrations: None, test_settings: Settings) -> DBConnectionManager:
    return DBConnectionManager(test_settings.SQLALCHEMY_DATABASE_URI)


@pytest.fixture(scope="session")
def read_engine(db_manager: DBConnectionManager) -> Generator[Engine, None, None]:
    engine = db_manager.get_engine(read_only=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def write_engine(db_manager: DBConnectionManager) -> Generator[Engine, None, None]:
    engine = db_manager.get_engine(read_only=False)
    yield engine
    engine.dispose()
