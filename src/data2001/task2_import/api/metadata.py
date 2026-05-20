from __future__ import annotations

from data2001.config import Settings
from data2001.task2_import.api.arcgis_client import ArcGISClient


def validate_metadata(client: ArcGISClient, settings: Settings, layer_names: list[str]) -> None:
    for name in layer_names:
        client.validate_layer_metadata(name, settings.api.layer(name))
