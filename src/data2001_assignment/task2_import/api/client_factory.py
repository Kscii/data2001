"""ArcGIS client 创建入口, 让 Task 2 的 API 调用使用同一种配置."""
from __future__ import annotations

from data2001_assignment.config import Settings
from data2001_assignment.task2_import.api.arcgis_client import ArcGISClient


def create_arcgis_client(settings: Settings) -> ArcGISClient:
    """根据项目配置创建 ArcGIS API 客户端."""
    return ArcGISClient(
        timeout_seconds=settings.api.timeout_seconds,
        max_retries=settings.api.max_retries,
        sleep_seconds=settings.api.sleep_seconds,
        page_size=settings.api.page_size,
    )
