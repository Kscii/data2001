"""Database setup, checks, and maintenance commands."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import Engine, text

from data2001.common.paths import SQL_DIR
from data2001.config import DatabaseSettings
from data2001.db.repositories.helpers import BUSINESS_TABLES


def schema_name(settings: DatabaseSettings) -> str:
    """Return the configured database schema name."""
    return settings.schema_name


def execute_sql_file(engine: Engine, path: Path, schema: str) -> None:
    """Read a SQL template file, replace the schema placeholder, and execute it."""
    with path.open("r", encoding="utf-8") as file:
        sql = file.read().format(schema=schema)
    with engine.begin() as connection:
        connection.execute(text(sql))


def init_database(engine: Engine, settings: DatabaseSettings) -> None:
    """Create extensions, schema, tables, and indexes."""
    for file_name in ["001_extensions.sql", "002_schema.sql", "003_indexes.sql"]:
        execute_sql_file(engine, SQL_DIR / file_name, schema_name(settings))


def reset_database(engine: Engine, settings: DatabaseSettings) -> None:
    """Drop the whole business schema and initialize it again."""
    with engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name(settings)}" CASCADE'))
    init_database(engine, settings)


def clear_database(engine: Engine, settings: DatabaseSettings) -> None:
    """Truncate business tables while keeping schema, tables, and indexes."""
    table_names = ", ".join(f'"{schema_name(settings)}"."{table}"' for table in BUSINESS_TABLES)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))


def check_database(engine: Engine, settings: DatabaseSettings, expected_srid: int) -> dict[str, Any]:
    """Check PostGIS, required tables, and geometry SRIDs."""
    schema = schema_name(settings)
    required_tables = set(BUSINESS_TABLES)
    with engine.connect() as connection:
        postgis_version = connection.execute(text("SELECT PostGIS_Version()")).scalar_one()
        tables = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = :schema
                    """
                ),
                {"schema": schema},
            )
        }
        srid_rows = connection.execute(
            text(
                """
                SELECT f_table_name, f_geometry_column, srid
                FROM geometry_columns
                WHERE f_table_schema = :schema
                ORDER BY f_table_name, f_geometry_column
                """
            ),
            {"schema": schema},
        ).mappings().all()

    missing_tables = sorted(required_tables.difference(tables))
    bad_srids = [dict(row) for row in srid_rows if row["srid"] != expected_srid]
    return {
        "postgis_version": postgis_version,
        "missing_tables": missing_tables,
        "bad_srids": bad_srids,
        "table_count": len(tables),
    }
