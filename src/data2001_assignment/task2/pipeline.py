"""Task 2 主流程：抓边界、抓 POI raw JSON、清洗入库、空间归属和收入入库."""
from __future__ import annotations

import sys
import time
from contextlib import nullcontext
from collections.abc import Iterable
from typing import Any

from alive_progress import alive_bar
from sqlalchemy import Engine

from data2001_assignment.analysis.income import fetch_sa2_income, normalise_income_feature
from data2001_assignment.common.progress import ProgressReporter
from data2001_assignment.config import Settings
from data2001_assignment.db.repositories import (
    assign_poi_to_sa2,
    upsert_clean_poi,
    upsert_income_records,
)
from data2001_assignment.task2.arcgis_client import ArcGISClient
from data2001_assignment.task2.boundaries import (
    fetch_boundaries,
    fetch_sa2_features_for_crawl,
    parse_boundaries,
)
from data2001_assignment.task2.cleaning import (
    clean_poi_feature,
    parse_population_feature,
)
from data2001_assignment.task2.json_file_store import (
    append_features_jsonl,
    iter_features_jsonl,
    prepare_poi_raw_files,
    write_raw_response_file,
)
from data2001_assignment.task2.loader import load_boundaries, load_population
from data2001_assignment.task2.metadata import validate_metadata
from data2001_assignment.task2.poi_client import build_poi_bbox_params, build_sa2_bbox_requests


def _report_bbox_progress(
    reporter: ProgressReporter | None,
    settings: Settings,
    current: int,
    total: int,
    source_name: str,
) -> None:
    """按配置间隔向终端报告 SA2 bbox 抓取进度."""
    if reporter is None:
        return
    interval = max(settings.progress.bbox_log_interval, 1)
    if current == total or current % interval == 0:
        reporter.detail(f"bbox {current}/{total} completed ({source_name})")


def _format_fetch_progress_text(
    current: int,
    total: int,
    source_name: str,
    request_pages: int,
    response_count: int,
    raw_feature_count: int,
) -> str:
    """生成 alive-progress 右侧显示的 POI 抓取状态文字."""
    return (
        f"req={current}/{total} "
        f"pages={request_pages} "
        f"responses={response_count} "
        f"features={raw_feature_count} "
        f"sa2={source_name}"
    )


def make_client(settings: Settings) -> ArcGISClient:
    """根据配置创建 ArcGIS API 客户端."""
    return ArcGISClient(
        timeout_seconds=settings.api.timeout_seconds,
        max_retries=settings.api.max_retries,
        sleep_seconds=settings.api.sleep_seconds,
        page_size=settings.api.page_size,
    )


def run_boundary_pipeline(engine: Engine, settings: Settings) -> dict[str, int]:
    """抓取并入库 SA4、SA2 边界和 SA2 population."""
    validate_metadata(settings, ["sa4", "sa2", "population"])
    client = make_client(settings)
    raw = fetch_boundaries(client, settings)
    parsed = parse_boundaries(raw)
    load_boundaries(engine, settings, parsed)

    population_layer = settings.api.layer("population")
    population_features = list(
        client.query_features(
            population_layer.url,
            {
                "where": "1=1",
                "outFields": ",".join(population_layer.out_fields),
                "returnGeometry": "false",
                "orderByFields": settings.population.sa2_code_field,
            },
            page_size=settings.api.page_size,
        )
    )
    load_population(
        engine,
        settings,
        [parse_population_feature(settings, feature) for feature in population_features],
    )
    return {
        "sa4": len(parsed["sa4"]),
        "sa2": len(parsed["sa2"]),
        "population": len(population_features),
    }


def _clean_and_load_features(
    engine: Engine,
    settings: Settings,
    features: Iterable[dict[str, Any]],
) -> int:
    """把 raw features 清洗并分批入库, 避免单次 executemany 太大."""
    clean_count = 0
    batch: list[dict[str, Any]] = []
    seen_objectids: set[Any] = set()
    for feature in features:
        record = clean_poi_feature(settings, feature)
        if record is None:
            continue
        objectid = record["objectid"]
        if objectid in seen_objectids:
            continue
        seen_objectids.add(objectid)
        batch.append(record)
        clean_count += 1
        if len(batch) >= settings.task2.clean_batch_size:
            upsert_clean_poi(engine, settings.database.schema_name, batch, settings.spatial.database_srid)
            batch = []
    upsert_clean_poi(engine, settings.database.schema_name, batch, settings.spatial.database_srid)
    return clean_count


def _assign_if_needed(engine: Engine, settings: Settings, clean_and_assign: bool) -> None:
    """在需要时执行 POI 到 SA2 的空间归属."""
    if clean_and_assign:
        assign_poi_to_sa2(engine, settings.database.schema_name, settings.spatial.assignment_method)


def fetch_poi_raw_and_clean(
    engine: Engine,
    settings: Settings,
    *,
    clean_and_assign: bool = True,
    reporter: ProgressReporter | None = None,
) -> dict[str, int]:
    """按 SA2 bbox 抓取 POI raw JSON, 并可选清洗入库和执行空间归属."""
    validate_metadata(settings, ["poi", "sa2"])
    client = make_client(settings)
    sa2_features = fetch_sa2_features_for_crawl(client, settings)
    requests = build_sa2_bbox_requests(sa2_features)
    poi_layer = settings.api.layer("poi")
    response_dir, features_path = prepare_poi_raw_files(settings)

    response_count = 0
    raw_feature_count = 0
    fetch_seconds = 0.0
    persist_seconds = 0.0
    clean_seconds = 0.0
    load_seconds = 0.0

    total_requests = len(requests)
    use_alive_progress = settings.progress.enabled and sys.stdout.isatty() and total_requests > 0
    progress_context = (
        alive_bar(total_requests, title="fetch-poi", bar="smooth")
        if use_alive_progress
        else nullcontext()
    )

    with progress_context as progress_bar:
        for request_index, request in enumerate(requests, start=1):
            base_params = build_poi_bbox_params(settings, request.bbox)
            request_pages = 0
            for offset, payload, page_fetch_seconds in client.iter_query_pages_with_timing(
                poi_layer.url,
                base_params,
                page_size=settings.api.page_size,
            ):
                fetch_seconds += page_fetch_seconds
                page_params = {
                    **base_params,
                    "f": "json",
                    "resultRecordCount": settings.api.page_size,
                    "resultOffset": offset,
                }
                response_count += 1
                request_pages += 1
                stage_start = time.perf_counter()
                write_raw_response_file(
                    response_dir,
                    sequence=response_count,
                    source_code=request.source_code,
                    offset=offset,
                    request_params=page_params,
                    payload=payload,
                )
                raw_feature_count += append_features_jsonl(features_path, payload.get("features", []))
                persist_seconds += time.perf_counter() - stage_start
                if progress_bar is not None:
                    progress_bar.text = _format_fetch_progress_text(
                        request_index,
                        total_requests,
                        request.source_name,
                        request_pages,
                        response_count,
                        raw_feature_count,
                    )

            if progress_bar is not None:
                progress_bar()
            else:
                _report_bbox_progress(reporter, settings, request_index, total_requests, request.source_name)

    clean_count = 0
    if clean_and_assign:
        stage_start = time.perf_counter()
        clean_count = _clean_and_load_features(engine, settings, iter_features_jsonl(settings))
        clean_seconds += time.perf_counter() - stage_start
    stage_start = time.perf_counter()
    _assign_if_needed(engine, settings, clean_and_assign)
    load_seconds += time.perf_counter() - stage_start
    return {
        "sa2_bbox_requests": len(requests),
        "raw_responses": response_count,
        "raw_features_seen": raw_feature_count,
        "clean_features_seen": clean_count,
        "fetch_seconds": fetch_seconds,
        "persist_seconds": persist_seconds,
        "clean_seconds": clean_seconds,
        "load_seconds": load_seconds,
    }


def load_income(engine: Engine, settings: Settings) -> int:
    """抓取并入库 SA2 median income 数据."""
    validate_metadata(settings, ["income"])
    client = make_client(settings)
    features = fetch_sa2_income(client, settings)
    records = [
        normalise_income_feature(feature, settings.income)
        for feature in features
    ]
    upsert_income_records(engine, settings.database.schema_name, records)
    return len(records)


def run_task2_pipeline(engine: Engine, settings: Settings) -> dict[str, int]:
    """运行 Task 2 的完整数据准备流程."""
    summary = run_boundary_pipeline(engine, settings)
    summary.update(fetch_poi_raw_and_clean(engine, settings))
    summary["income"] = load_income(engine, settings)
    return summary
