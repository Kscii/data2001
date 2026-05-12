"""Task 2 入库函数, 把解析后的边界和人口记录写入 PostgreSQL/PostGIS."""
from __future__ import annotations

from sqlalchemy import Engine

from data2001_assignment.config import Settings
from data2001_assignment.db.repositories import (
    update_sa2_population,
    upsert_sa2_records,
    upsert_sa4_records,
)


def load_boundaries(engine: Engine, settings: Settings, parsed: dict[str, list[dict]]) -> None:
    """把 parse_boundaries 的结果写入数据库."""
    schema = settings.database.schema_name
    upsert_sa4_records(engine, schema, parsed["sa4"], settings.spatial.database_srid)
    upsert_sa2_records(engine, schema, parsed["sa2"], settings.spatial.database_srid)


def load_population(engine: Engine, settings: Settings, records: list[dict]) -> None:
    """把 SA2 population 数据更新到 sa2 表."""
    update_sa2_population(engine, settings.database.schema_name, records)
