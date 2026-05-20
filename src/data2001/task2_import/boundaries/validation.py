"""Boundary validation checks for Task 2 SA4/SA2 membership."""
from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, text

from data2001.common.types import StepSummary
from data2001.config import Settings


MIN_SA2_SA4_COVERAGE_RATIO = 0.999


def load_sa2_sa4_membership_validation(
    engine: Engine,
    settings: Settings,
    *,
    min_coverage_ratio: float = MIN_SA2_SA4_COVERAGE_RATIO,
) -> list[dict[str, Any]]:
    schema = settings.database.schema_name
    sql = text(
        f"""
        WITH normalized_sa2 AS (
            SELECT
                sa2_code,
                sa2_name,
                sa4_code,
                sa4_name,
                ST_Multi(ST_CollectionExtract(ST_MakeValid(geometry), 3)) AS geometry
            FROM {schema}.sa2
        ),
        normalized_sa4 AS (
            SELECT
                sa4_code,
                sa4_name,
                ST_Multi(ST_CollectionExtract(ST_MakeValid(geometry), 3)) AS geometry
            FROM {schema}.sa4
        ),
        metrics AS (
            SELECT
                sa2.sa2_code,
                sa2.sa2_name,
                sa2.sa4_code,
                sa2.sa4_name,
                sa4.sa4_code AS parent_sa4_code,
                sa4.sa4_name AS parent_sa4_name,
                COALESCE(
                    ST_Covers(sa4.geometry, ST_PointOnSurface(sa2.geometry)),
                    false
                ) AS point_on_surface_covered,
                CAST(
                    COALESCE(
                        ST_Area(ST_Intersection(sa4.geometry, sa2.geometry))
                        / NULLIF(ST_Area(sa2.geometry), 0),
                        0.0
                    ) AS double precision
                ) AS coverage_ratio
            FROM normalized_sa2 sa2
            LEFT JOIN normalized_sa4 sa4
              ON sa4.sa4_code = sa2.sa4_code
        )
        SELECT
            *,
            (
                parent_sa4_code IS NOT NULL
                AND point_on_surface_covered
                AND coverage_ratio >= :min_coverage_ratio
            ) AS is_valid,
            CASE
                WHEN parent_sa4_code IS NULL THEN 'missing_parent_sa4'
                WHEN point_on_surface_covered
                 AND coverage_ratio >= :min_coverage_ratio THEN 'valid'
                WHEN point_on_surface_covered THEN 'low_coverage_ratio'
                WHEN coverage_ratio >= :min_coverage_ratio THEN 'surface_point_outside_sa4'
                ELSE 'outside_sa4'
            END AS validation_status
        FROM metrics
        ORDER BY sa4_name, sa2_name
        """
    )
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                sql,
                {"min_coverage_ratio": min_coverage_ratio},
            ).mappings()
        ]


def summarize_sa2_sa4_membership_validation(
    rows: list[dict[str, Any]],
    *,
    min_coverage_ratio: float = MIN_SA2_SA4_COVERAGE_RATIO,
) -> StepSummary:
    """Summarise row-level SA2-to-SA4 validation into pipeline output fields."""
    valid_rows = [row for row in rows if row["is_valid"]]
    invalid_rows = [row for row in rows if not row["is_valid"]]
    coverage_ratios = [float(row["coverage_ratio"]) for row in rows]
    selected_sa4_codes = {
        str(row["parent_sa4_code"])
        for row in rows
        if row.get("parent_sa4_code") is not None
    }
    return {
        "boundary_selected_sa4": len(selected_sa4_codes),
        "boundary_sa2_checked": len(rows),
        "boundary_sa2_valid": len(valid_rows),
        "boundary_sa2_invalid": len(invalid_rows),
        "boundary_min_coverage_ratio": min(coverage_ratios) if coverage_ratios else 0.0,
        "boundary_coverage_threshold": min_coverage_ratio,
        "boundary_point_failures": sum(
            1 for row in rows if not row["point_on_surface_covered"]
        ),
        "boundary_missing_parent_sa4": sum(
            1 for row in rows if row["parent_sa4_code"] is None
        ),
    }


def _format_invalid_examples(rows: list[dict[str, Any]], *, limit: int = 5) -> str:
    """Format a compact invalid-row sample for validation errors."""
    examples = []
    for row in rows[:limit]:
        examples.append(
            "{sa2_code} {sa2_name} -> {sa4_name} "
            "status={validation_status} coverage={coverage_ratio:.6f}".format(
                sa2_code=row["sa2_code"],
                sa2_name=row["sa2_name"],
                sa4_name=row["sa4_name"],
                validation_status=row["validation_status"],
                coverage_ratio=float(row["coverage_ratio"]),
            )
        )
    return "; ".join(examples)


def validate_sa2_sa4_membership(
    engine: Engine,
    settings: Settings,
    *,
    min_coverage_ratio: float = MIN_SA2_SA4_COVERAGE_RATIO,
    raise_on_invalid: bool = True,
) -> StepSummary:
    rows = load_sa2_sa4_membership_validation(
        engine,
        settings,
        min_coverage_ratio=min_coverage_ratio,
    )
    summary = summarize_sa2_sa4_membership_validation(
        rows,
        min_coverage_ratio=min_coverage_ratio,
    )
    if not rows:
        raise ValueError("SA2/SA4 boundary validation found no imported SA2 rows")

    invalid_rows = [row for row in rows if not row["is_valid"]]
    if invalid_rows and raise_on_invalid:
        examples = _format_invalid_examples(invalid_rows)
        raise ValueError(
            "SA2/SA4 boundary validation failed: "
            f"invalid_sa2_count={len(invalid_rows)}; examples={examples}"
        )
    return summary
