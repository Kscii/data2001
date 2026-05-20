"""Database read queries used by workflows and visuals."""
from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, text


def select_score_input(
    engine: Engine,
    schema: str,
    score_universe: str,
    selected_sa4_names: list[str],
) -> list[dict[str, Any]]:
    """Select SA2 population and POI counts for score calculation."""
    if score_universe == "selected_sa4" and selected_sa4_names:
        placeholders = ", ".join(f":sa4_name_{index}" for index in range(len(selected_sa4_names)))
        where_clause = f"WHERE s.sa4_name IN ({placeholders})"
        params: dict[str, Any] = {
            f"sa4_name_{index}": name
            for index, name in enumerate(selected_sa4_names)
        }
    else:
        where_clause = ""
        params = {}

    sql = text(
        f"""
        SELECT
            s.sa2_code,
            s.sa2_name,
            s.sa4_code,
            s.sa4_name,
            s.population,
            CAST(COUNT(sp.poi_objectid) AS integer) AS poi_count
        FROM {schema}.sa2 s
        LEFT JOIN {schema}.sa2_poi sp
          ON sp.sa2_code = s.sa2_code
        {where_clause}
        GROUP BY s.sa2_code, s.sa2_name, s.sa4_code, s.sa4_name, s.population
        ORDER BY s.sa4_name, s.sa2_name
        """
    )
    with engine.connect() as connection:
        return [dict(row) for row in connection.execute(sql, params).mappings()]


def select_score_income_sample(
    engine: Engine,
    schema: str,
    *,
    score_version: str,
    score_universe: str,
) -> list[dict[str, Any]]:
    """Select score-income rows for the correlation test."""
    sql = text(
        f"""
        SELECT
            score.sa2_code,
            score.score_100 AS score,
            score.population,
            income.median_income_2022_23,
            income.income_earners_2022_23
        FROM {schema}.sa2_score score
        JOIN {schema}.sa2_income income
          ON income.sa2_code = score.sa2_code
        WHERE score.score_version = :score_version
          AND score.score_universe = :score_universe
        """
    )
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                sql,
                {"score_version": score_version, "score_universe": score_universe},
            ).mappings()
        ]
