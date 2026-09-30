from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.settings import settings


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def connect_database() -> psycopg.Connection:
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def apply_migrations() -> None:
    for migration_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if migration_path.name.endswith(".down.sql"):
            continue
        with connect_database() as connection:
            connection.execute(migration_path.read_text(encoding="utf-8"), prepare=False)