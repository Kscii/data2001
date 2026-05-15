"""Task 4 数据加载接口, 供 notebook、export 和 dashboard 统一调用.

命名规则:
  load_*(engine, settings) → DataFrame  数据库查询
  load_*(settings)         → DataFrame  文件系统检查（无 engine）
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import Engine, text

from data2001.common.paths import resolve_project_path
from data2001.config import Settings
from data2001.db.repositories.helpers import BUSINESS_TABLES
from data2001.db.repositories.read import select_score_input
from data2001.task2_import.boundaries.areas import selected_sa4_names


# ── 可视化数据 ──────────────────────────────────────────────────────────────


def load_sa2_scores(engine: Engine, settings: Settings) -> pd.DataFrame:
    """读取带 SA2 geometry 的 score 数据, 仅限指定 SA4 范围."""
    schema = settings.database.schema_name
    sa4_names = selected_sa4_names(settings)
    sa4_list = ", ".join(f"'{name.replace(chr(39), chr(39)*2)}'" for name in sa4_names)
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
          AND area.sa4_name IN ({sa4_list})
        ORDER BY area.sa4_name, area.sa2_name
        """
    )
    with engine.connect() as connection:
        return pd.DataFrame(
            connection.execute(
                sql,
                {
                    "score_version": settings.task3_score.score_version,
                    "score_universe": settings.task3_score.score_universe,
                },
            ).mappings().all()
        )


def load_poi_group_counts(engine: Engine, settings: Settings) -> pd.DataFrame:
    """按 POI group 聚合 POI 数量, 仅限指定 SA4 范围."""
    schema = settings.database.schema_name
    sa4_names = selected_sa4_names(settings)
    sa4_list = ", ".join(f"'{name.replace(chr(39), chr(39)*2)}'" for name in sa4_names)
    sql = text(
        f"""
        SELECT
            COALESCE(p.poigroup_name, 'Unknown') AS poigroup_name,
            p.poigroup_code,
            COUNT(*)::integer AS poi_count
        FROM {schema}.poi_clean p
        LEFT JOIN {schema}.sa2_poi assigned
          ON assigned.poi_objectid = p.objectid
        LEFT JOIN {schema}.sa2 area
          ON area.sa2_code = assigned.sa2_code
        WHERE area.sa4_name IN ({sa4_list})
        GROUP BY p.poigroup_name, p.poigroup_code
        ORDER BY poi_count DESC, poigroup_name
        """
    )
    with engine.connect() as connection:
        return pd.DataFrame(connection.execute(sql).mappings().all())


def load_poi_points(
    engine: Engine,
    settings: Settings,
    *,
    limit: int | None = None,
) -> pd.DataFrame:
    """读取 POI 点位及其 SA2/SA4 归属信息, 仅限指定 SA4 范围."""
    schema = settings.database.schema_name
    limit_clause = "LIMIT :limit" if limit is not None else ""
    sa4_names = selected_sa4_names(settings)
    sa4_list = ", ".join(f"'{name.replace(chr(39), chr(39)*2)}'" for name in sa4_names)
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
          AND area.sa4_name IN ({sa4_list})
        ORDER BY poi.objectid
        {limit_clause}
        """
    )
    with engine.connect() as connection:
        params = {"limit": limit} if limit is not None else {}
        return pd.DataFrame(connection.execute(sql, params).mappings().all())


def load_score_income(engine: Engine, settings: Settings) -> pd.DataFrame:
    """读取 score 与 median income 已 join 的数据, 仅限指定 SA4 范围."""
    schema = settings.database.schema_name
    sa4_names = selected_sa4_names(settings)
    sa4_list = ", ".join(f"'{name.replace(chr(39), chr(39)*2)}'" for name in sa4_names)
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
          AND area.sa4_name IN ({sa4_list})
        ORDER BY area.sa4_name, area.sa2_name
        """
    )
    with engine.connect() as connection:
        return pd.DataFrame(
            connection.execute(
                sql,
                {
                    "score_version": settings.task3_score.score_version,
                    "score_universe": settings.task3_score.score_universe,
                },
            ).mappings().all()
        )


def load_correlation_results(engine: Engine, settings: Settings) -> pd.DataFrame:
    """读取 score-income correlation 检验结果."""
    schema = settings.database.schema_name
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
        return pd.DataFrame(
            connection.execute(
                sql,
                {
                    "score_version": settings.task3_score.score_version,
                    "score_universe": settings.task3_score.score_universe,
                },
            ).mappings().all()
        )


# ── Rubric 证据 ─────────────────────────────────────────────────────────────


def load_table_counts(engine: Engine, settings: Settings) -> pd.DataFrame:
    """返回核心业务表的行数汇总."""
    schema = settings.database.schema_name
    rows: list[dict[str, int | str]] = []
    with engine.connect() as connection:
        for table_name in reversed(BUSINESS_TABLES):
            count = connection.execute(
                text(f"SELECT COUNT(*) FROM {schema}.{table_name}")
            ).scalar_one()
            rows.append({"table_name": table_name, "row_count": int(count)})
    return pd.DataFrame(rows)


def load_schema_summary(engine: Engine, settings: Settings) -> pd.DataFrame:
    """返回字段级 schema 详情, 用于 report/database 证据."""
    schema = settings.database.schema_name
    sql = text(
        """
        SELECT
            c.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            tc.constraint_type
        FROM information_schema.columns c
        LEFT JOIN information_schema.key_column_usage kcu
          ON kcu.table_schema = c.table_schema
         AND kcu.table_name = c.table_name
         AND kcu.column_name = c.column_name
        LEFT JOIN information_schema.table_constraints tc
          ON tc.constraint_schema = kcu.constraint_schema
         AND tc.constraint_name = kcu.constraint_name
        WHERE c.table_schema = :schema
        ORDER BY c.table_name, c.ordinal_position
        """
    )
    with engine.connect() as connection:
        return pd.DataFrame(
            connection.execute(sql, {"schema": schema}).mappings().all()
        )


def load_index_summary(engine: Engine, settings: Settings) -> pd.DataFrame:
    """返回 PostgreSQL index 定义, 用于 indexing rubric 证据."""
    schema = settings.database.schema_name
    sql = text(
        """
        SELECT tablename AS table_name, indexname AS index_name, indexdef AS definition
        FROM pg_indexes
        WHERE schemaname = :schema
        ORDER BY tablename, indexname
        """
    )
    with engine.connect() as connection:
        return pd.DataFrame(
            connection.execute(sql, {"schema": schema}).mappings().all()
        )


def load_spatial_join_summary(engine: Engine, settings: Settings) -> pd.DataFrame:
    """汇总 POI 到 SA2 的 spatial join 质量及边界重复处理情况."""
    schema = settings.database.schema_name
    sql = text(
        f"""
        WITH candidates AS (
            SELECT p.objectid, COUNT(s.sa2_code)::integer AS candidate_sa2_count
            FROM {schema}.poi_clean p
            JOIN {schema}.sa2 s
              ON ST_Covers(s.geometry, p.geometry)
            GROUP BY p.objectid
        ),
        assigned AS (
            SELECT COUNT(DISTINCT poi_objectid)::integer AS assigned_poi
            FROM {schema}.sa2_poi
        )
        SELECT
            (SELECT COUNT(*)::integer FROM {schema}.poi_clean) AS clean_poi,
            assigned.assigned_poi,
            ((SELECT COUNT(*)::integer FROM {schema}.poi_clean) - assigned.assigned_poi) AS unassigned_poi,
            (SELECT COUNT(*)::integer FROM candidates WHERE candidate_sa2_count > 1) AS boundary_duplicate_candidates,
            (SELECT COUNT(*)::integer FROM {schema}.sa2_poi) AS assignment_rows
        FROM assigned
        """
    )
    with engine.connect() as connection:
        return pd.DataFrame(connection.execute(sql).mappings().all())


def load_score_input_summary(engine: Engine, settings: Settings) -> pd.DataFrame:
    """汇总 z-score/sigmoid 计算前的 score input 行."""
    rows = select_score_input(
        engine,
        settings.database.schema_name,
        settings.task3_score.score_universe,
        selected_sa4_names(settings),
    )
    data = pd.DataFrame(rows)
    if data.empty:
        return pd.DataFrame(
            [
                {
                    "sa2_count": 0,
                    "total_poi": 0,
                    "mean_poi_count": 0.0,
                    "std_poi_count": 0.0,
                    "min_poi_count": 0,
                    "max_poi_count": 0,
                    "below_min_population": 0,
                    "missing_population": 0,
                }
            ]
        )
    return pd.DataFrame(
        [
            {
                "sa2_count": int(len(data)),
                "total_poi": int(data["poi_count"].sum()),
                "mean_poi_count": float(data["poi_count"].mean()),
                "std_poi_count": float(data["poi_count"].std(ddof=0)),
                "min_poi_count": int(data["poi_count"].min()),
                "max_poi_count": int(data["poi_count"].max()),
                "below_min_population": int(
                    (data["population"] < settings.task3_score.min_population).sum()
                ),
                "missing_population": int(data["population"].isna().sum()),
            }
        ]
    )


def load_correlation_summary(engine: Engine, settings: Settings) -> pd.DataFrame:
    """返回最新 correlation 检验行及简洁显著性标签."""
    schema = settings.database.schema_name
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
        result = pd.DataFrame(
            connection.execute(
                sql,
                {
                    "score_version": settings.task3_score.score_version,
                    "score_universe": settings.task3_score.score_universe,
                },
            ).mappings().all()
        )
    if not result.empty:
        result["interpretation"] = result["is_significant"].map(
            {True: "statistically significant", False: "not statistically significant"}
        )
    return result


# ── 文件系统检查 ─────────────────────────────────────────────────────────────


def load_api_extraction_summary(settings: Settings) -> pd.DataFrame:
    """汇总 Task 2 API 抓取产生的原始 POI 文件."""
    response_dir = resolve_project_path(settings.outputs.raw_poi_response_dir)
    features_path = resolve_project_path(settings.outputs.raw_poi_features_jsonl)
    response_files = (
        sorted(response_dir.glob("response_*.json")) if response_dir.exists() else []
    )
    feature_rows = 0
    if features_path.exists():
        with features_path.open("r", encoding="utf-8") as file:
            feature_rows = sum(1 for _ in file)
    return pd.DataFrame(
        [
            {
                "response_dir": str(response_dir),
                "response_file_count": len(response_files),
                "features_jsonl": str(features_path),
                "raw_feature_rows": feature_rows,
                "features_file_exists": features_path.exists(),
                "features_file_size_mb": round(
                    features_path.stat().st_size / 1024 / 1024, 2
                )
                if features_path.exists()
                else 0.0,
            }
        ]
    )


def expected_report_figure_paths(settings: Settings) -> pd.DataFrame:
    """列出 Task 4 export 步骤预期生成的 report 图片文件."""
    charts_dir = resolve_project_path(settings.outputs.charts_dir)
    file_names = [
        "score_histogram.png",
        "top_sa2_score.png",
        "bottom_sa2_score.png",
        "poi_group_distribution.png",
        "score_income_correlation.png",
        "sa2_score_choropleth.png",
        "poi_point_scatter.png",
    ]
    rows = []
    for file_name in file_names:
        path = charts_dir / file_name
        rows.append(
            {
                "figure": file_name,
                "path": str(Path(settings.outputs.charts_dir) / file_name),
                "exists": path.exists(),
            }
        )
    return pd.DataFrame(rows)
