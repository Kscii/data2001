from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from data2001.config import Settings
from data2001.task2_import.boundaries.areas import BBox, bbox_from_arcgis_geometry
from data2001.task2_import.records import ArcGISFeature


@dataclass(frozen=True)
class POIFetchRequest:
    source_level: str
    source_code: str
    source_name: str
    bbox: BBox


def build_poi_bbox_params(settings: Settings, bbox: BBox) -> dict[str, Any]:
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
