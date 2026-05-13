"""可视化查询层, 向 notebook、report 和 Dash 返回显式展示记录."""
from __future__ import annotations

from sqlalchemy import Engine, text

from data2001_assignment.task4_visuals.records import (
    CorrelationResultView,
    PoiGroupCountView,
    PoiPointView,
    Sa2ScoreView,
    ScoreIncomeView,
)


def select_sa2_scores(
    engine: Engine,
    schema: str,
    *,
    score_version: str,
    score_universe: str,
) -> list[Sa2ScoreView]:
    """读取带 SA2 geometry 的 score 数据, 用于图表和地图."""
    sql = text(
        f"""
        SELECT
            s.sa2_code,
            area.sa2_name,
            area.sa4_code,
            area.sa4_name,
            area.population,
            s.poi_count,
            s.mean_poi_count,
            s.std_poi_count,
            s.z_poi,
            s.score_raw,
            s.score_100,
            ST_AsGeoJSON(area.geometry)::json AS geometry
        FROM {schema}.sa2_score s
        JOIN {schema}.sa2 area
          ON area.sa2_code = s.sa2_code
        WHERE s.score_version = :score_version
          AND s.score_universe = :score_universe
        ORDER BY area.sa4_name, area.sa2_name
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {"score_version": score_version, "score_universe": score_universe},
        ).mappings().all()
    return [Sa2ScoreView.from_row(dict(row)) for row in rows]


def select_poi_group_counts(engine: Engine, schema: str) -> list[PoiGroupCountView]:
    """按 POI group 聚合 POI 数量."""
    sql = text(
        f"""
        SELECT
            COALESCE(poigroup_name, 'Unknown') AS poigroup_name,
            poigroup_code,
            COUNT(*)::integer AS poi_count
        FROM {schema}.poi_clean
        GROUP BY poigroup_name, poigroup_code
        ORDER BY poi_count DESC, poigroup_name
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(sql).mappings().all()
    return [PoiGroupCountView.from_row(dict(row)) for row in rows]


def select_poi_points(engine: Engine, schema: str, *, limit: int | None = None) -> list[PoiPointView]:
    """读取 POI 点位及其 SA2/SA4 归属信息."""
    limit_clause = "LIMIT :limit" if limit is not None else ""
    sql = text(
        f"""
        SELECT
            poi.objectid,
            poi.poigroup_code,
            COALESCE(poi.poigroup_name, 'Unknown') AS poigroup_name,
            poi.poitype,
            poi.poiname,
            poi.longitude,
            poi.latitude,
            area.sa2_code,
            area.sa2_name,
            area.sa4_code,
            area.sa4_name
        FROM {schema}.poi_clean poi
        LEFT JOIN {schema}.sa2_poi assigned
          ON assigned.poi_objectid = poi.objectid
        LEFT JOIN {schema}.sa2 area
          ON area.sa2_code = assigned.sa2_code
        WHERE poi.longitude IS NOT NULL
          AND poi.latitude IS NOT NULL
        ORDER BY poi.objectid
        {limit_clause}
        """
    )
    with engine.connect() as connection:
        params = {"limit": limit} if limit is not None else {}
        rows = connection.execute(sql, params).mappings().all()
    return [PoiPointView.from_row(dict(row)) for row in rows]


def select_score_income(
    engine: Engine,
    schema: str,
    *,
    score_version: str,
    score_universe: str,
) -> list[ScoreIncomeView]:
    """读取 score 与 median income 已 join 的数据."""
    sql = text(
        f"""
        SELECT
            score.sa2_code,
            area.sa2_name,
            area.sa4_name,
            score.score_100,
            score.poi_count,
            score.population,
            income.median_income_2022_23,
            income.income_earners_2022_23
        FROM {schema}.sa2_score score
        JOIN {schema}.sa2 area
          ON area.sa2_code = score.sa2_code
        JOIN {schema}.sa2_income income
          ON income.sa2_code = score.sa2_code
        WHERE score.score_version = :score_version
          AND score.score_universe = :score_universe
        ORDER BY area.sa4_name, area.sa2_name
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {"score_version": score_version, "score_universe": score_universe},
        ).mappings().all()
    return [ScoreIncomeView.from_row(dict(row)) for row in rows]


def select_correlation_results(
    engine: Engine,
    schema: str,
    *,
    score_version: str,
    score_universe: str,
) -> list[CorrelationResultView]:
    """读取 score-income correlation 检验结果."""
    sql = text(
        f"""
        SELECT method, statistic, p_value, n, alpha, is_significant, created_at
        FROM (
            SELECT DISTINCT ON (method)
                method, statistic, p_value, n, alpha, is_significant, created_at
            FROM {schema}.score_income_correlation
            WHERE score_version = :score_version
              AND score_universe = :score_universe
            ORDER BY method, created_at DESC
        ) latest
        ORDER BY method
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(
            sql,
            {"score_version": score_version, "score_universe": score_universe},
        ).mappings().all()
    return [CorrelationResultView.from_row(dict(row)) for row in rows]
