from __future__ import annotations

from dataclasses import dataclass

from data2001.config import Settings
from data2001.task2_import.boundaries.areas import fetch_sa2_features_for_crawl, fetch_sa4_features
from data2001.task2_import.api.client_factory import create_arcgis_client
from data2001.task2_import.api.metadata import validate_metadata
from data2001.task2_import.poi.poi_requests import POIFetchRequest, build_sa2_bbox_requests


@dataclass(frozen=True)
class CrawlPlan:
    scope: str
    sa4_count: int
    sa2_count: int
    request_count: int
    requests: list[POIFetchRequest]


def build_crawl_plan(settings: Settings) -> CrawlPlan:
    client = create_arcgis_client(settings)
    validate_metadata(client, settings, ["sa4", "sa2"])
    sa4_features = fetch_sa4_features(client, settings)
    sa2_features = fetch_sa2_features_for_crawl(client, settings)
    requests = build_sa2_bbox_requests(sa2_features)
    return CrawlPlan(
        scope=settings.task2_import.crawl_scope,
        sa4_count=len(sa4_features),
        sa2_count=len(sa2_features),
        request_count=len(requests),
        requests=requests,
    )
