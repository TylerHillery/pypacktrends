import inspect
from pathlib import Path

from sqlalchemy import Engine, text

from app.core.logger import logger


def read_sql_file(sql_file: Path) -> tuple[str, ...]:
    if not sql_file.exists():
        raise FileNotFoundError(f"{sql_file} is missing.")

    with open(sql_file, "r") as f:
        contents = f.read().strip()

    sql_statements = tuple(
        statement.strip() for statement in contents.split(";") if statement.strip()
    )

    if not sql_statements:
        raise ValueError(
            f"The file '{sql_file}' exists but contains no SQL statements."
        )

    return sql_statements


def get_sql_migration_file() -> Path:
    caller_frame = inspect.stack()[1]
    caller_function_name = caller_frame.function
    version_file = Path(caller_frame.filename)

    if caller_function_name not in ("upgrade", "downgrade"):
        raise ValueError(
            f"Function '{caller_function_name}' is not a valid Alembic migration function. "
            "Expected 'upgrade' or 'downgrade'."
        )

    return version_file.parent / f"{version_file.stem}_{caller_function_name}.sql"


def run_sql_statements(write_engine: Engine, sql_file: Path) -> tuple[str, ...]:
    executed_statements = []
    with write_engine.begin() as conn:
        for sql in read_sql_file(sql_file):
            try:
                logger.info(f"Executing SQL: {sql}")
                conn.execute(text(sql))
                executed_statements.append(sql)
            except Exception as e:
                logger.error(f"Failed to execute SQL: {sql}. Error: {e}")
                raise e
    return tuple(executed_statements)
