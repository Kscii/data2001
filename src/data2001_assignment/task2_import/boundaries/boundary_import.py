"""Task 2 boundary import：抓取 SA4/SA2 边界和 SA2 population 并写库."""
from __future__ import annotations

from sqlalchemy import Engine

from data2001_assignment.common.types import StepSummary
from data2001_assignment.config import Settings
from data2001_assignment.task2_import.api.client_factory import create_arcgis_client
from data2001_assignment.task2_import.api.metadata import validate_metadata
from data2001_assignment.task2_import.boundaries.areas import fetch_boundaries, parse_boundaries
from data2001_assignment.task2_import.boundaries.database_load import write_area_records, write_population_records
from data2001_assignment.task2_import.poi.cleaning import parse_population_feature


def run_boundary_import(engine: Engine, settings: Settings) -> StepSummary:
    """抓取并入库 SA4、SA2 边界和 SA2 population."""
    client = create_arcgis_client(settings)
    validate_metadata(client, settings, ["sa4", "sa2", "population"])

    boundary_records = parse_boundaries(fetch_boundaries(client, settings))
    write_area_records(engine, settings, boundary_records)

    population_layer = settings.api.layer("population")
    population_features = list(
        client.query_features(
            population_layer.url,
            {
                "where": "1=1",
                "outFields": ",".join(population_layer.out_fields),
                "returnGeometry": "false",
                "orderByFields": settings.population.sa2_code_field,
            },
            page_size=settings.api.page_size,
        )
    )
    population_records = [
        parse_population_feature(settings, feature)
        for feature in population_features
    ]
    write_population_records(engine, settings, population_records)

    return {
        "sa4": len(boundary_records.sa4),
        "sa2": len(boundary_records.sa2),
        "population": len(population_records),
    }
