"""SA4/SA2 boundary 抓取、bbox 计算和数据库记录解析."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from data2001_assignment.config import Settings
from data2001_assignment.task2.arcgis_client import ArcGISClient


@dataclass(frozen=True)
class BBox:
    """ArcGIS bbox 范围对象, 用于构造 envelope 查询参数."""
    minx: float
    miny: float
    maxx: float
    maxy: float

    def to_arcgis_envelope(self) -> str:
        """把 bbox 转成 ArcGIS envelope 参数字符串, 用于 ArcGIS API 查询参数."""
        return f"{self.minx},{self.miny},{self.maxx},{self.maxy}"

    def as_dict(self) -> dict[str, float]:
        """把 bbox 转成数据库入库字段字典."""
        return {
            "bbox_minx": self.minx,
            "bbox_miny": self.miny,
            "bbox_maxx": self.maxx,
            "bbox_maxy": self.maxy,
        }


def _quote_values(values: list[str]) -> str:
    """把字符串列表安全拼成 SQL IN 条件使用的值."""
    escaped = [value.replace("'", "''") for value in values]
    return ", ".join(f"'{value}'" for value in escaped)


def selected_sa4_names(settings: Settings) -> list[str]:
    """从 unikey -> SA4 映射中取出去重后的 SA4 名称."""
    names = [
        name.strip()
        for name in settings.task2.selected_sa4_by_member.values()
        if name and name.strip()
    ]
    return sorted(set(names))


def build_sa4_where_clause(settings: Settings) -> str:
    """根据配置决定当前需要处理哪些 SA4."""
    task2 = settings.task2
    if task2.crawl_scope == "greater_sydney":
        escaped_gccsa = task2.gccsa_name.replace("'", "''")
        return f"gccsa_name_2021 = '{escaped_gccsa}'"

    if task2.crawl_scope == "explicit_sa4_codes":
        if not task2.sa4_codes:
            raise ValueError("crawl_scope=explicit_sa4_codes 时必须配置 task2.sa4_codes")
        return f"sa4_code_2021 IN ({_quote_values(task2.sa4_codes)})"

    names = selected_sa4_names(settings)
    if not names:
        raise ValueError("crawl_scope=selected_sa4 时必须配置 selected_sa4_by_member")
    return f"sa4_name_2021 IN ({_quote_values(names)})"


def fetch_sa4_features(client: ArcGISClient, settings: Settings) -> list[dict[str, Any]]:
    """从 ABS ArcGIS API 抓取当前 scope 下的 SA4 features."""
    layer = settings.api.layer("sa4")
    params = {
        "where": build_sa4_where_clause(settings),
        "outFields": ",".join(layer.out_fields),
        "returnGeometry": "true",
        "outSR": settings.api.out_sr,
        "orderByFields": "sa4_name_2021",
    }
    return list(client.query_features(layer.url, params))


def fetch_sa2_features_for_crawl(client: ArcGISClient, settings: Settings) -> list[dict[str, Any]]:
    """抓取当前 scope 下的 SA2；后续 POI 按这些 SA2 的 bbox 逐个请求."""
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


def fetch_boundaries(client: ArcGISClient, settings: Settings) -> dict[str, list[dict[str, Any]]]:
    """请求 SA4/SA2 boundary 原始 features."""
    return {
        "sa4": fetch_sa4_features(client, settings),
        "sa2": fetch_sa2_features_for_crawl(client, settings),
    }


def bbox_from_arcgis_geometry(geometry: dict[str, Any]) -> BBox:
    """从 ArcGIS polygon/point geometry 中计算 bbox."""
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
    """把 ArcGIS rings 转成 GeoJSON Polygon.

    PostGIS 入库时会用 ST_Multi 包成 MultiPolygon.这里保留 rings 原始顺序, 
    不在 Python 中判断内外环, 避免引入额外空间库.
    """
    rings = geometry.get("rings")
    if not rings:
        raise ValueError("ArcGIS polygon geometry 缺少 rings")
    return {"type": "Polygon", "coordinates": rings}


def parse_boundaries(raw: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    """把 boundary raw features 解析成数据库字段."""
    sa4_records: list[dict[str, Any]] = []
    for feature in raw["sa4"]:
        attrs = feature["attributes"]
        bbox = bbox_from_arcgis_geometry(feature["geometry"])
        sa4_records.append(
            {
                "sa4_code": attrs.get("sa4_code_2021"),
                "sa4_name": attrs.get("sa4_name_2021"),
                "gccsa_code": attrs.get("gccsa_code_2021"),
                "gccsa_name": attrs.get("gccsa_name_2021"),
                "state_code": attrs.get("state_code_2021"),
                "state_name": attrs.get("state_name_2021"),
                "area_albers_sqkm": attrs.get("area_albers_sqkm"),
                "asgs_loci_uri": attrs.get("asgs_loci_uri_2021"),
                "geometry_geojson": arcgis_polygon_to_geojson(feature["geometry"]),
                **bbox.as_dict(),
            }
        )

    sa2_records: list[dict[str, Any]] = []
    for feature in raw["sa2"]:
        attrs = feature["attributes"]
        bbox = bbox_from_arcgis_geometry(feature["geometry"])
        sa2_records.append(
            {
                "sa2_code": attrs.get("sa2_code_2021"),
                "sa2_name": attrs.get("sa2_name_2021"),
                "sa3_code": attrs.get("sa3_code_2021"),
                "sa3_name": attrs.get("sa3_name_2021"),
                "sa4_code": attrs.get("sa4_code_2021"),
                "sa4_name": attrs.get("sa4_name_2021"),
                "gccsa_code": attrs.get("gccsa_code_2021"),
                "gccsa_name": attrs.get("gccsa_name_2021"),
                "state_code": attrs.get("state_code_2021"),
                "state_name": attrs.get("state_name_2021"),
                "area_albers_sqkm": attrs.get("area_albers_sqkm"),
                "asgs_loci_uri": attrs.get("asgs_loci_uri_2021"),
                "geometry_geojson": arcgis_polygon_to_geojson(feature["geometry"]),
                **bbox.as_dict(),
            }
        )

    return {"sa4": sa4_records, "sa2": sa2_records}
