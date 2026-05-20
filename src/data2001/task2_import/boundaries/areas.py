from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from data2001.config import Settings
from data2001.task2_import.api.arcgis_client import ArcGISClient
from data2001.task2_import.records import (
    ArcGISFeature,
    BoundaryRecords,
    Sa2AreaRecord,
    Sa4AreaRecord,
)


@dataclass(frozen=True)
class BBox:
    minx: float
    miny: float
    maxx: float
    maxy: float

    def to_arcgis_envelope(self) -> str:
        return f"{self.minx},{self.miny},{self.maxx},{self.maxy}"


def _quote_values(values: list[str]) -> str:
    escaped = [value.replace("'", "''") for value in values]
    return ", ".join(f"'{value}'" for value in escaped)


def selected_sa4_names(settings: Settings) -> list[str]:
    names = [
        name.strip()
        for name in settings.task2_import.selected_sa4_by_member.values()
        if name and name.strip()
    ]
    return sorted(set(names))


def build_sa4_where_clause(settings: Settings) -> str:
    task2 = settings.task2_import
    if task2.crawl_scope == "greater_sydney":
        escaped_gccsa = task2.gccsa_name.replace("'", "''")
        return f"gccsa_name_2021 = '{escaped_gccsa}'"

    if task2.crawl_scope == "explicit_sa4_codes":
        if not task2.sa4_codes:
            raise ValueError("crawl_scope=explicit_sa4_codes 时必须配置 task2_import.sa4_codes")
        return f"sa4_code_2021 IN ({_quote_values(task2.sa4_codes)})"

    names = selected_sa4_names(settings)
    if not names:
        raise ValueError("crawl_scope=selected_sa4 时必须配置 selected_sa4_by_member")
    return f"sa4_name_2021 IN ({_quote_values(names)})"


def fetch_sa4_features(client: ArcGISClient, settings: Settings) -> list[ArcGISFeature]:
    layer = settings.api.layer("sa4")
    params = {
        "where": build_sa4_where_clause(settings),
        "outFields": ",".join(layer.out_fields),
        "returnGeometry": "true",
        "outSR": settings.api.out_sr,
        "orderByFields": "sa4_name_2021",
    }
    return list(client.query_features(layer.url, params))


def fetch_sa2_features_for_crawl(client: ArcGISClient, settings: Settings) -> list[ArcGISFeature]:
    layer = settings.api.layer("sa2")
    sa4_where = build_sa4_where_clause(settings)
    params = {
        "where": sa4_where,
        "outFields": ",".join(layer.out_fields),
        "returnGeometry": "true",
        "outSR": settings.api.out_sr,
        "orderByFields": "sa4_name_2021,sa2_name_2021",
    }
    return list(client.query_features(layer.url, params))


def fetch_boundaries(client: ArcGISClient, settings: Settings) -> dict[str, list[ArcGISFeature]]:
    return {
        "sa4": fetch_sa4_features(client, settings),
        "sa2": fetch_sa2_features_for_crawl(client, settings),
    }


def bbox_from_arcgis_geometry(geometry: dict[str, Any]) -> BBox:
    if "rings" in geometry: 
        xs = [point[0] for ring in geometry["rings"] for point in ring]
        ys = [point[1] for ring in geometry["rings"] for point in ring]
    elif "x" in geometry and "y" in geometry:
        xs = [geometry["x"]]
        ys = [geometry["y"]]
    else:
        raise ValueError("无法从 ArcGIS geometry 计算 bbox")
    return BBox(min(xs), min(ys), max(xs), max(ys))


def arcgis_polygon_to_geojson(geometry: dict[str, Any]) -> dict[str, Any]:
    rings = geometry.get("rings")
    if not rings:
        raise ValueError("ArcGIS polygon geometry 缺少 rings")
    return {"type": "Polygon", "coordinates": rings}


def parse_boundaries(raw: dict[str, list[ArcGISFeature]]) -> BoundaryRecords:
    sa4_records: list[Sa4AreaRecord] = []
    for feature in raw["sa4"]:
        attrs = feature["attributes"]
        bbox = bbox_from_arcgis_geometry(feature["geometry"])
        sa4_records.append(
            Sa4AreaRecord(
                sa4_code=attrs.get("sa4_code_2021"),
                sa4_name=attrs.get("sa4_name_2021"),
                gccsa_code=attrs.get("gccsa_code_2021"),
                gccsa_name=attrs.get("gccsa_name_2021"),
                state_code=attrs.get("state_code_2021"),
                state_name=attrs.get("state_name_2021"),
                area_albers_sqkm=attrs.get("area_albers_sqkm"),
                asgs_loci_uri=attrs.get("asgs_loci_uri_2021"),
                geometry_geojson=arcgis_polygon_to_geojson(feature["geometry"]),
                bbox_minx=bbox.minx,
                bbox_miny=bbox.miny,
                bbox_maxx=bbox.maxx,
                bbox_maxy=bbox.maxy,
            )
        )

    sa2_records: list[Sa2AreaRecord] = []
    for feature in raw["sa2"]:
        attrs = feature["attributes"]
        bbox = bbox_from_arcgis_geometry(feature["geometry"])
        sa2_records.append(
            Sa2AreaRecord(
                sa2_code=attrs.get("sa2_code_2021"),
                sa2_name=attrs.get("sa2_name_2021"),
                sa3_code=attrs.get("sa3_code_2021"),
                sa3_name=attrs.get("sa3_name_2021"),
                sa4_code=attrs.get("sa4_code_2021"),
                sa4_name=attrs.get("sa4_name_2021"),
                gccsa_code=attrs.get("gccsa_code_2021"),
                gccsa_name=attrs.get("gccsa_name_2021"),
                state_code=attrs.get("state_code_2021"),
                state_name=attrs.get("state_name_2021"),
                area_albers_sqkm=attrs.get("area_albers_sqkm"),
                asgs_loci_uri=attrs.get("asgs_loci_uri_2021"),
                geometry_geojson=arcgis_polygon_to_geojson(feature["geometry"]),
                bbox_minx=bbox.minx,
                bbox_miny=bbox.miny,
                bbox_maxx=bbox.maxx,
                bbox_maxy=bbox.maxy,
            )
        )

    return BoundaryRecords(sa4=sa4_records, sa2=sa2_records)
