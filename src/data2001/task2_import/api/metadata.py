"""ArcGIS metadata 检查, 确保远端字段、geometry type 和 SRID 符合项目默认配置."""
from __future__ import annotations

from data2001.config import Settings
from data2001.task2_import.api.arcgis_client import ArcGISClient


def validate_metadata(client: ArcGISClient, settings: Settings, layer_names: list[str]) -> None:
    """按配置检查远端 ArcGIS layer metadata."""
    for name in layer_names:
        client.validate_layer_metadata(name, settings.api.layer(name))
