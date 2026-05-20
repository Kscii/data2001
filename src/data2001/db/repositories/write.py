"""Database write commands used by import and score workflows."""
from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, text

from data2001.db.repositories.helpers import none_if_nan, to_json


def upsert_sa4_records(engine: Engine, schema: str, records: list[dict[str, Any]], srid: int) -> None:
    """Insert or update SA4 area records."""
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
    payload = [{**record, "geometry_geojson": to_json(record["geometry_geojson"]), "srid": srid} for record in records]
    with engine.begin() as connection:
        connection.execute(sql, payload)


def upsert_sa2_records(engine: Engine, schema: str, records: list[dict[str, Any]], srid: int) -> None:
    """Insert or update SA2 area records."""
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
        ON CONFLICT (sa2_code) DO UPDATE SET  -- 如果sa2_code冲突了, 就更新这条记录的其他字段为新值
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
    payload = [{**record, "geometry_geojson": to_json(record["geometry_geojson"]), "srid": srid} for record in records]
    with engine.begin() as connection:
        connection.execute(sql, payload)


def update_sa2_population(engine: Engine, schema: str, records: list[dict[str, Any]]) -> None:
    """Update SA2 population fields."""
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


def upsert_poi_records(engine: Engine, schema: str, records: list[dict[str, Any]], srid: int) -> None:
    """Insert clean POI records."""
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
    """Assign every POI to one SA2 with ST_Covers."""
    insert_sql = text(
        f"""
        -- ST_Covers keeps POI points that lie exactly on a SA2 boundary.
        -- If one POI matches multiple SA2 polygons, choose the first SA2 code.
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
        connection.execute(text(f"TRUNCATE TABLE {schema}.sa2_poi"))
        connection.execute(insert_sql, {"assignment_method": assignment_method})


def upsert_scores(engine: Engine, schema: str, records: list[dict[str, Any]]) -> None:
    """Insert or update SA2 score records."""
    if not records:
        return
    payload = [
        {
            **record,
            "poi_count": int(record["poi_count"]),
            "population": none_if_nan(record.get("population")),
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
    """Insert or update SA2 income records."""
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


def insert_correlation_results(engine: Engine, schema: str, records: list[dict[str, Any]]) -> None:
    """Insert score-income correlation results."""
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
