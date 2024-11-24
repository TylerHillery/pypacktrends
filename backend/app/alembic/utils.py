import logging
import inspect
from pathlib import Path

from sqlalchemy import text

from app.core.db import db_manager

logger = logging.getLogger("alembic.runtime.migration")


def run_sql_statements() -> None:
    engine = db_manager.get_engine(readonly=False)
    version_file = Path(inspect.stack()[1].filename)
    caller_name = inspect.stack()[1].function
    sql_file = version_file.parent / f"{version_file.stem}_{caller_name}.sql"

    if not sql_file.exists():
        err_msg = (
            f"{sql_file} is missing. Cannot proceed with the {caller_name} migration."
        )
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    with open(sql_file, "r") as f:
        contents = f.read().strip()

    sql_statements = [
        statement.strip() for statement in contents.split(";") if statement.strip()
    ]

    if not sql_statements:
        err_msg = f"The file '{sql_file}' exists but contains no SQL statements."
        logger.error(err_msg)
        raise ValueError(err_msg)

    with engine.begin() as conn:
        for sql in sql_statements:
            try:
                logger.info(f"Executing SQL: {sql}")
                conn.execute(text(sql))
            except Exception as e:
                logger.error(f"Failed to execute SQL: {sql}. Error: {e}")
                raise e
