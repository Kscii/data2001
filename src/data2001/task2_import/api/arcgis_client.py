from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import requests

from data2001.config import LayerSettings
from data2001.task2_import.records import ArcGISFeature, ArcGISPayload


@dataclass(frozen=True)
class ArcGISClient:
    timeout_seconds: int
    max_retries: int
    sleep_seconds: float
    page_size: int

    def get_json(self, url: str, params: dict[str, Any]) -> ArcGISPayload:
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=self.timeout_seconds)
                response.raise_for_status()
                payload = response.json()
                if "error" in payload:
                    raise RuntimeError(f"ArcGIS error: {payload['error']}")
                return payload
            except Exception as exc: 
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(self.sleep_seconds * (attempt + 1))
        raise RuntimeError(f"ArcGIS request failed after retries: {url}") from last_error

    def get_metadata(self, layer: LayerSettings) -> ArcGISPayload:
        return self.get_json(layer.metadata_url, {"f": "json"})

    def validate_layer_metadata(self, name: str, layer: LayerSettings) -> ArcGISPayload:
        metadata = self.get_metadata(layer)
        fields = {field["name"] for field in metadata.get("fields", [])}
        missing_fields = sorted(set(layer.expected_fields).difference(fields))
        if missing_fields:
            raise ValueError(f"{name} metadata 缺少字段: {missing_fields}")

        geometry_type = metadata.get("geometryType")
        if layer.geometry_type and geometry_type != layer.geometry_type:
            raise ValueError(
                f"{name} geometry type 不一致: expected={layer.geometry_type}, actual={geometry_type}"
            )

        if layer.expected_srid:
            spatial_reference = (
                metadata.get("extent", {}).get("spatialReference")
                or metadata.get("spatialReference")
                or {}
            )
            actual_srid = spatial_reference.get("latestWkid") or spatial_reference.get("wkid")
            if actual_srid != layer.expected_srid:
                raise ValueError(
                    f"{name} SRID 不一致: expected={layer.expected_srid}, actual={actual_srid}"
                )

        return metadata

    def iter_query_pages(
        self,
        url: str,
        params: dict[str, Any],
        *,
        page_size: int | None = None,
    ) -> Iterator[tuple[int, ArcGISPayload]]:
        for offset, payload, _fetch_seconds in self.iter_query_pages_with_timing(
            url,
            params,
            page_size=page_size,
        ):
            yield offset, payload

    def iter_query_pages_with_timing(
        self,
        url: str,
        params: dict[str, Any],
        *,
        page_size: int | None = None,
    ) -> Iterator[tuple[int, ArcGISPayload, float]]:
        offset = 0
        limit = page_size or self.page_size

        while True:
            page_params = {
                **params,
                "f": params.get("f", "json"),
                "resultRecordCount": limit,
                "resultOffset": offset,
            }
            start = time.perf_counter()
            payload = self.get_json(url, page_params)
            fetch_seconds = time.perf_counter() - start
            yield offset, payload, fetch_seconds

            features = payload.get("features", [])
            if not payload.get("exceededTransferLimit") or len(features) < limit:
                break
            offset += limit

    def query_features(
        self,
        url: str,
        params: dict[str, Any],
        *,
        page_size: int | None = None,
    ) -> Iterator[ArcGISFeature]:
        offset = 0
        limit = page_size or self.page_size

        while True:
            page_params = {
                **params,
                "f": params.get("f", "json"),
                "resultRecordCount": limit,
                "resultOffset": offset,
            }
            payload = self.get_json(url, page_params)
            features = payload.get("features", [])
            for feature in features:
                yield feature

            if not payload.get("exceededTransferLimit") or len(features) < limit:
                break
            offset += limit
