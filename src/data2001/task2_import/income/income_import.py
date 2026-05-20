from __future__ import annotations

from sqlalchemy import Engine

from data2001.config import Settings
from data2001.db.repositories.write import upsert_income_records
from data2001.task2_import.api.client_factory import create_arcgis_client
from data2001.task2_import.api.metadata import validate_metadata
from data2001.task2_import.income.income import fetch_sa2_income, normalize_income_feature
from data2001.task2_import.records import income_records_to_db_rows


def run_income_import(engine: Engine, settings: Settings) -> int:
    client = create_arcgis_client(settings)
    validate_metadata(client, settings, ["income"])
    features = fetch_sa2_income(client, settings)
    records = [
        normalize_income_feature(feature, settings.income)
        for feature in features
    ]
    upsert_income_records(engine, settings.database.schema_name, income_records_to_db_rows(records))
    return len(records)
