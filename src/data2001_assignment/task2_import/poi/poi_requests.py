"""POI 查询参数和 bbox 抓取请求构建工具."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from data2001_assignment.config import Settings
from data2001_assignment.task2_import.api.arcgis_client import ArcGISClient
from data2001_assignment.task2_import.boundaries.areas import BBox, bbox_from_arcgis_geometry
from data2001_assignment.task2_import.records import ArcGISFeature


@dataclass(frozen=True)
class POIFetchRequest:
    """一次 POI bbox 抓取请求的来源和范围."""
    source_level: str
    source_code: str
    source_name: str
    bbox: BBox


def build_poi_bbox_params(settings: Settings, bbox: BBox) -> dict[str, Any]:
    """构造 NSW POI bbox 查询参数.bbox 只生成候选 POI, 最终归属仍靠 SA2 polygon."""
    layer = settings.api.layer("poi")
    return {
        "where": "1=1",
        "outFields": ",".join(layer.out_fields),
        "returnGeometry": "true",
        "geometry": bbox.to_arcgis_envelope(),
        "geometryType": "esriGeometryEnvelope",
        "inSR": settings.api.out_sr,
        "outSR": settings.api.out_sr,
        "spatialRel": "esriSpatialRelIntersects",
        "orderByFields": "objectid",
    }


def build_sa2_bbox_requests(sa2_features: list[ArcGISFeature]) -> list[POIFetchRequest]:
    """特定 SA4 或 Greater Sydney 抓取时, 都按 SA2 bbox 逐个抓 POI."""
    requests: list[POIFetchRequest] = []
    for feature in sa2_features:
        attrs = feature["attributes"]
        requests.append(
            POIFetchRequest(
                source_level="SA2",
                source_code=attrs["sa2_code_2021"],
                source_name=attrs["sa2_name_2021"],
                bbox=bbox_from_arcgis_geometry(feature["geometry"]),
            )
        )
    return requests


def fetch_poi_within_bbox(
    client: ArcGISClient,
    settings: Settings,
    bbox: BBox,
) -> list[ArcGISFeature]:
    """作业要求的通用函数：返回一个 bbox 内的所有 POI."""
    params = build_poi_bbox_params(settings, bbox)
    return list(client.query_features(settings.api.layer("poi").url, params, page_size=settings.api.page_size))
