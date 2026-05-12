"""抓取计划生成工具, 用于 plan-crawl 展示将要请求的 SA4、SA2 和 bbox."""
from __future__ import annotations

from dataclasses import dataclass

from data2001_assignment.config import Settings
from data2001_assignment.task2.arcgis_client import ArcGISClient
from data2001_assignment.task2.boundaries import fetch_sa2_features_for_crawl, fetch_sa4_features
from data2001_assignment.task2.metadata import validate_metadata
from data2001_assignment.task2.poi_client import POIFetchRequest, build_sa2_bbox_requests


@dataclass(frozen=True)
class CrawlPlan:
    """根据配置展开后的抓取计划摘要."""
    scope: str
    sa4_count: int
    sa2_count: int
    request_count: int
    requests: list[POIFetchRequest]


def build_crawl_plan(settings: Settings) -> CrawlPlan:
    """根据 YAML scope 生成 POI 抓取计划.

    关键约定：只要是基于 SA4 的任务, 实际抓取都展开为该 SA4 下每个 SA2 的 bbox.
    """
    validate_metadata(settings, ["sa4", "sa2"])
    client = ArcGISClient(
        timeout_seconds=settings.api.timeout_seconds,
        max_retries=settings.api.max_retries,
        sleep_seconds=settings.api.sleep_seconds,
        page_size=settings.api.page_size,
    )
    sa4_features = fetch_sa4_features(client, settings)
    sa2_features = fetch_sa2_features_for_crawl(client, settings)
    requests = build_sa2_bbox_requests(sa2_features)
    return CrawlPlan(
        scope=settings.task2.crawl_scope,
        sa4_count=len(sa4_features),
        sa2_count=len(sa2_features),
        request_count=len(requests),
        requests=requests,
    )
