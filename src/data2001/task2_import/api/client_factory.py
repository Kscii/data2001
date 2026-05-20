from __future__ import annotations

from data2001.config import Settings
from data2001.task2_import.api.arcgis_client import ArcGISClient


def create_arcgis_client(settings: Settings) -> ArcGISClient:
    return ArcGISClient(
        timeout_seconds=settings.api.timeout_seconds,
        max_retries=settings.api.max_retries,
        sleep_seconds=settings.api.sleep_seconds,
        page_size=settings.api.page_size,
    )
