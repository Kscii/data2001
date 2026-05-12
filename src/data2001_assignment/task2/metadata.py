"""ArcGIS metadata gate, 确保远端字段、geometry type 和 SRID 符合 YAML 契约."""
from __future__ import annotations

from data2001_assignment.config import Settings
from data2001_assignment.task2.arcgis_client import ArcGISClient


def validate_metadata(settings: Settings, layer_names: list[str]) -> None:
    """按配置检查远端 ArcGIS layer metadata."""
    client = ArcGISClient(
        timeout_seconds=settings.api.timeout_seconds,
        max_retries=settings.api.max_retries,
        sleep_seconds=settings.api.sleep_seconds,
        page_size=settings.api.page_size,
    )
    for name in layer_names:
        client.validate_layer_metadata(name, settings.api.layer(name))
