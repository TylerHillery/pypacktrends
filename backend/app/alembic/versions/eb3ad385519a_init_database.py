"""init database

Revision ID: eb3ad385519a
Revises:
Create Date: 2024-11-21 16:39:50.473545

"""

from typing import Sequence, Union

from app.alembic.utils import get_sql_migration_file, run_sql_statements
from app.core.db import write_engine

# revision identifiers, used by Alembic.
revision: str = "eb3ad385519a"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    run_sql_statements(write_engine, get_sql_migration_file())


def downgrade() -> None:
    run_sql_statements(write_engine, get_sql_migration_file())
