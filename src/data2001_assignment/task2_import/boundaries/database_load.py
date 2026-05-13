"""Task 2 入库函数, 把解析后的边界和人口记录写入 PostgreSQL/PostGIS."""
from __future__ import annotations

from sqlalchemy import Engine

from data2001_assignment.config import Settings
from data2001_assignment.db.repositories.write import (
    update_sa2_population,
    upsert_sa2_records,
    upsert_sa4_records,
)
from data2001_assignment.task2_import.records import (
    BoundaryRecords,
    Sa2PopulationRecord,
    population_records_to_db_rows,
    sa2_records_to_db_rows,
    sa4_records_to_db_rows,
)


def write_area_records(engine: Engine, settings: Settings, records: BoundaryRecords) -> None:
    """Write parsed SA4 and SA2 area records to the database."""
    schema = settings.database.schema_name
    upsert_sa4_records(engine, schema, sa4_records_to_db_rows(records.sa4), settings.spatial.database_srid)
    upsert_sa2_records(engine, schema, sa2_records_to_db_rows(records.sa2), settings.spatial.database_srid)


def write_population_records(engine: Engine, settings: Settings, records: list[Sa2PopulationRecord]) -> None:
    """Write SA2 population records to the database."""
    update_sa2_population(engine, settings.database.schema_name, population_records_to_db_rows(records))
