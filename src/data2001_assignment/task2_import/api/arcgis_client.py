"""ArcGIS REST 客户端, 集中处理请求、metadata 校验、分页和计数查询."""
from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import requests

from data2001_assignment.config import LayerSettings
from data2001_assignment.task2_import.records import ArcGISFeature, ArcGISPayload


@dataclass(frozen=True)
class ArcGISClient:
    """ArcGIS REST API 客户端, 封装请求、重试、分页和 metadata 获取."""
    timeout_seconds: int
    max_retries: int
    sleep_seconds: float
    page_size: int

    def get_json(self, url: str, params: dict[str, Any]) -> ArcGISPayload:
        """发送 ArcGIS REST 请求, 并把服务端 error 统一转成异常."""
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
        """读取 layer metadata, 用于在请求前确认字段契约没有变化."""
        return self.get_json(layer.metadata_url, {"f": "json"})

    def validate_layer_metadata(self, name: str, layer: LayerSettings) -> ArcGISPayload:
        """校验 ArcGIS layer 的字段、geometry type 和 SRID.

        如果远端接口字段变化, workflow 必须停止, 避免用错误字段生成数据库结果.
        """
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
        """按页返回完整 payload, 供 raw response 持久化使用."""
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
        """按页返回 payload 和本页请求耗时, 供 workflow 汇总阶段耗时."""
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
        """按 resultOffset 分页返回 feature."""
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

    def query_count(self, url: str, params: dict[str, Any]) -> int:
        """返回符合条件的记录数, 用于抓取前估算任务量."""
        payload = self.get_json(
            url,
            {
                **params,
                "f": "json",
                "returnCountOnly": "true",
                "returnGeometry": "false",
            },
        )
        return int(payload.get("count", 0))
