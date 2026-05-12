"""数据库 repository 函数, 集中封装表初始化、upsert、查询和维护操作."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, text

from data2001_assignment.common.paths import SQL_DIR
from data2001_assignment.config import DatabaseSettings


BUSINESS_TABLES = [
    "score_income_correlation",
    "sa2_score",
    "sa2_income",
    "sa2_poi",
    "poi_clean",
    "sa2",
    "sa4",
]


def _schema(settings: DatabaseSettings) -> str:
    """返回当前数据库 schema 名称."""
    return settings.schema_name


def execute_sql_file(engine: Engine, path: Path, schema: str) -> None:
    """读取 SQL 模板文件, 替换 schema 后执行."""
    with path.open("r", encoding="utf-8") as file:
        sql = file.read().format(schema=schema)
    with engine.begin() as connection:
        connection.execute(text(sql))


def init_database(engine: Engine, settings: DatabaseSettings) -> None:
    """按顺序执行 extensions、schema 和 indexes SQL 文件."""
    for file_name in ["001_extensions.sql", "002_schema.sql", "003_indexes.sql"]:
        execute_sql_file(engine, SQL_DIR / file_name, _schema(settings))


def reset_database(engine: Engine, settings: DatabaseSettings) -> None:
    """删除整个业务 schema 后重新初始化数据库."""
    with engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{_schema(settings)}" CASCADE'))
    init_database(engine, settings)


def clear_database(engine: Engine, settings: DatabaseSettings) -> None:
    """清空所有业务表内容, 但保留 schema、表和索引."""
    table_names = ", ".join(f'"{_schema(settings)}"."{table}"' for table in BUSINESS_TABLES)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))


def count_table_rows(engine: Engine, schema: str, table_name: str) -> int:
    """统计指定表的行数."""
    with engine.connect() as connection:
        return int(connection.execute(text(f"SELECT COUNT(*) FROM {schema}.{table_name}")).scalar_one())


def check_database(engine: Engine, settings: DatabaseSettings, expected_srid: int) -> dict[str, Any]:
    """检查 PostGIS、必需表和 geometry SRID 是否正常."""
    schema = _schema(settings)
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
    bad_srids = [
        dict(row)
        for row in srid_rows
        if row["srid"] != expected_srid
    ]
    return {
        "postgis_version": postgis_version,
        "missing_tables": missing_tables,
        "bad_srids": bad_srids,
        "table_count": len(tables),
    }


def _to_json(value: Any) -> str:
    """把 Python 对象序列化成稳定的 JSON 字符串."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _none_if_nan(value: Any) -> Any:
    """把 NaN 转成 None, 方便写入数据库."""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def upsert_sa4_records(engine: Engine, schema: str, records: list[dict[str, Any]], srid: int) -> None:
    """插入或更新SA4、records相关逻辑."""
    if not records:
        return
    sql = text(
        f"""
        INSERT INTO {schema}.sa4 (
            sa4_code, sa4_name, gccsa_code, gccsa_name, state_code, state_name,
            area_albers_sqkm, asgs_loci_uri, bbox_minx, bbox_miny, bbox_maxx, bbox_maxy,
            geometry
        )
        VALUES (
            :sa4_code, :sa4_name, :gccsa_code, :gccsa_name, :state_code, :state_name,
            :area_albers_sqkm, :asgs_loci_uri, :bbox_minx, :bbox_miny, :bbox_maxx, :bbox_maxy,
            ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geometry_geojson), :srid))
        )
        ON CONFLICT (sa4_code) DO UPDATE SET
            sa4_name = EXCLUDED.sa4_name,
            gccsa_code = EXCLUDED.gccsa_code,
            gccsa_name = EXCLUDED.gccsa_name,
            state_code = EXCLUDED.state_code,
            state_name = EXCLUDED.state_name,
            area_albers_sqkm = EXCLUDED.area_albers_sqkm,
            asgs_loci_uri = EXCLUDED.asgs_loci_uri,
            bbox_minx = EXCLUDED.bbox_minx,
            bbox_miny = EXCLUDED.bbox_miny,
            bbox_maxx = EXCLUDED.bbox_maxx,
            bbox_maxy = EXCLUDED.bbox_maxy,
            geometry = EXCLUDED.geometry,
            loaded_at = now()
        """
    )
    payload = [{**record, "geometry_geojson": _to_json(record["geometry_geojson"]), "srid": srid} for record in records]
    with engine.begin() as connection:
        connection.execute(sql, payload)


def upsert_sa2_records(engine: Engine, schema: str, records: list[dict[str, Any]], srid: int) -> None:
    """插入或更新SA2、records相关逻辑."""
    if not records:
        return
    sql = text(
        f"""
        INSERT INTO {schema}.sa2 (
            sa2_code, sa2_name, sa3_code, sa3_name, sa4_code, sa4_name,
            gccsa_code, gccsa_name, state_code, state_name, area_albers_sqkm,
            asgs_loci_uri, bbox_minx, bbox_miny, bbox_maxx, bbox_maxy, geometry
        )
        VALUES (
            :sa2_code, :sa2_name, :sa3_code, :sa3_name, :sa4_code, :sa4_name,
            :gccsa_code, :gccsa_name, :state_code, :state_name, :area_albers_sqkm,
            :asgs_loci_uri, :bbox_minx, :bbox_miny, :bbox_maxx, :bbox_maxy,
            ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geometry_geojson), :srid))
        )
        ON CONFLICT (sa2_code) DO UPDATE SET
            sa2_name = EXCLUDED.sa2_name,
            sa3_code = EXCLUDED.sa3_code,
            sa3_name = EXCLUDED.sa3_name,
            sa4_code = EXCLUDED.sa4_code,
            sa4_name = EXCLUDED.sa4_name,
            gccsa_code = EXCLUDED.gccsa_code,
            gccsa_name = EXCLUDED.gccsa_name,
            state_code = EXCLUDED.state_code,
            state_name = EXCLUDED.state_name,
            area_albers_sqkm = EXCLUDED.area_albers_sqkm,
            asgs_loci_uri = EXCLUDED.asgs_loci_uri,
            bbox_minx = EXCLUDED.bbox_minx,
            bbox_miny = EXCLUDED.bbox_miny,
            bbox_maxx = EXCLUDED.bbox_maxx,
            bbox_maxy = EXCLUDED.bbox_maxy,
            geometry = EXCLUDED.geometry,
            loaded_at = now()
        """
    )
    payload = [{**record, "geometry_geojson": _to_json(record["geometry_geojson"]), "srid": srid} for record in records]
    with engine.begin() as connection:
        connection.execute(sql, payload)


def update_sa2_population(engine: Engine, schema: str, records: list[dict[str, Any]]) -> None:
    """更新SA2、population相关逻辑."""
    if not records:
        return
    sql = text(
        f"""
        UPDATE {schema}.sa2
        SET population = :population,
            population_density = :population_density,
            loaded_at = now()
        WHERE sa2_code = :sa2_code
        """
    )
    with engine.begin() as connection:
        connection.execute(sql, records)


def upsert_clean_poi(engine: Engine, schema: str, records: list[dict[str, Any]], srid: int) -> None:
    """插入或更新clean、POI相关逻辑."""
    if not records:
        return
    payload = []
    seen_objectids: set[int] = set()
    for record in records:
        objectid = record.get("objectid")
        if objectid is None or objectid in seen_objectids:
            continue
        seen_objectids.add(objectid)
        payload.append({**record, "srid": srid})
    if not payload:
        return
    sql = text(
        f"""
        INSERT INTO {schema}.poi_clean (
            objectid, topoid, poigroup_code, poigroup_name, poitype, poiname,
            poilabel, poilabeltype, poialtlabel, poisourcefeatureoid, accesscontrol,
            startdate, enddate, lastupdate, msoid, centroidid, shapeuuid,
            changetype, processstate, urbanity, longitude, latitude, geometry
        )
        VALUES (
            :objectid, :topoid, :poigroup_code, :poigroup_name, :poitype, :poiname,
            :poilabel, :poilabeltype, :poialtlabel, :poisourcefeatureoid, :accesscontrol,
            :startdate, :enddate, :lastupdate, :msoid, :centroidid, :shapeuuid,
            :changetype, :processstate, :urbanity, :longitude, :latitude,
            ST_SetSRID(ST_MakePoint(:longitude, :latitude), :srid)
        )
        ON CONFLICT (objectid) DO NOTHING
        """
    )
    with engine.begin() as connection:
        connection.execute(sql, payload)


def assign_poi_to_sa2(engine: Engine, schema: str, assignment_method: str) -> None:
    """用 ST_Covers 把每个 POI 确定性归属到一个 SA2."""
    sql = text(
        f"""
        TRUNCATE TABLE {schema}.sa2_poi;

        -- ST_Covers 保证落在 SA2 边界上的 POI 不会被丢弃.
        -- 如果一个 POI 同时匹配多个 SA2, 这里按 sa2_code 升序确定性选择第一个；
        -- 这样避免 score 重复计数, 但边界点归属仍带有任意性.
        INSERT INTO {schema}.sa2_poi (sa2_code, poi_objectid, assign_method)
        SELECT sa2_code, objectid, :assignment_method
        FROM (
            SELECT
                s.sa2_code,
                p.objectid,
                ROW_NUMBER() OVER (PARTITION BY p.objectid ORDER BY s.sa2_code ASC) AS rn
            FROM {schema}.poi_clean p
            JOIN {schema}.sa2 s
              ON ST_Covers(s.geometry, p.geometry)
        ) ranked
        WHERE rn = 1;
        """
    )
    with engine.begin() as connection:
        connection.execute(sql, {"assignment_method": assignment_method})


def load_score_input(engine: Engine, schema: str, score_universe: str, selected_sa4_names: list[str]) -> list[dict[str, Any]]:
    """读取 score 计算需要的 SA2 population 和 POI count."""
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
            COUNT(sp.poi_objectid)::integer AS poi_count
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


def upsert_scores(engine: Engine, schema: str, records: list[dict[str, Any]]) -> None:
    """把计算好的 SA2 score upsert 到 sa2_score 表."""
    if not records:
        return
    payload = [
        {
            **record,
            "poi_count": int(record["poi_count"]),
            "population": _none_if_nan(record.get("population")),
        }
        for record in records
    ]
    sql = text(
        f"""
        INSERT INTO {schema}.sa2_score (
            score_version, score_universe, sa2_code, poi_count,
            mean_poi_count, std_poi_count, z_poi, score_raw, score_100,
            population
        )
        VALUES (
            :score_version, :score_universe, :sa2_code, :poi_count,
            :mean_poi_count, :std_poi_count, :z_poi, :score_raw, :score_100,
            :population
        )
        ON CONFLICT (sa2_code, score_version, score_universe) DO UPDATE SET
            poi_count = EXCLUDED.poi_count,
            mean_poi_count = EXCLUDED.mean_poi_count,
            std_poi_count = EXCLUDED.std_poi_count,
            z_poi = EXCLUDED.z_poi,
            score_raw = EXCLUDED.score_raw,
            score_100 = EXCLUDED.score_100,
            population = EXCLUDED.population,
            created_at = now()
        """
    )
    with engine.begin() as connection:
        connection.execute(sql, payload)


def upsert_income_records(engine: Engine, schema: str, records: list[dict[str, Any]]) -> None:
    """把 SA2 median income 记录 upsert 到 sa2_income 表."""
    if not records:
        return
    with engine.connect() as connection:
        existing_sa2_codes = {
            row[0]
            for row in connection.execute(text(f"SELECT sa2_code FROM {schema}.sa2"))
        }
    records = [
        record
        for record in records
        if record.get("sa2_code") in existing_sa2_codes
    ]
    if not records:
        return
    sql = text(
        f"""
        INSERT INTO {schema}.sa2_income (
            sa2_code, sa2_name, income_earners_2022_23, income_earners_2021_22,
            income_earners_change, income_earners_change_pct, median_income_2022_23,
            source_year, source_name
        )
        VALUES (
            :sa2_code, :sa2_name, :income_earners_2022_23, :income_earners_2021_22,
            :income_earners_change, :income_earners_change_pct, :median_income_2022_23,
            :source_year, :source_name
        )
        ON CONFLICT (sa2_code) DO UPDATE SET
            sa2_name = EXCLUDED.sa2_name,
            income_earners_2022_23 = EXCLUDED.income_earners_2022_23,
            income_earners_2021_22 = EXCLUDED.income_earners_2021_22,
            income_earners_change = EXCLUDED.income_earners_change,
            income_earners_change_pct = EXCLUDED.income_earners_change_pct,
            median_income_2022_23 = EXCLUDED.median_income_2022_23,
            source_year = EXCLUDED.source_year,
            source_name = EXCLUDED.source_name,
            loaded_at = now()
        """
    )
    with engine.begin() as connection:
        connection.execute(sql, records)


def load_score_income_sample(
    engine: Engine,
    schema: str,
    *,
    score_version: str,
    score_universe: str,
) -> list[dict[str, Any]]:
    """读取 correlation 检验需要的 score-income 样本."""
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


def insert_correlation_results(engine: Engine, schema: str, records: list[dict[str, Any]]) -> None:
    """插入相关性、results相关逻辑."""
    if not records:
        return
    sql = text(
        f"""
        INSERT INTO {schema}.score_income_correlation (
            score_version, score_universe, method, statistic, p_value, n, alpha, is_significant
        )
        VALUES (
            :score_version, :score_universe, :method, :statistic, :p_value, :n, :alpha, :is_significant
        )
        """
    )
    with engine.begin() as connection:
        connection.execute(sql, records)
