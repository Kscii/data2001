from __future__ import annotations

import sys
import time
from collections.abc import Iterable
from contextlib import nullcontext
from typing import Any

from alive_progress import alive_bar
from sqlalchemy import Engine

from data2001.common.progress import ProgressReporter
from data2001.common.types import StepSummary
from data2001.config import Settings
from data2001.db.repositories.write import assign_poi_to_sa2, upsert_poi_records
from data2001.task2_import.api.client_factory import create_arcgis_client
from data2001.task2_import.api.metadata import validate_metadata
from data2001.task2_import.boundaries.areas import fetch_sa2_features_for_crawl
from data2001.task2_import.poi.cleaning import clean_poi_feature
from data2001.task2_import.poi.poi_requests import build_poi_bbox_params, build_sa2_bbox_requests
from data2001.task2_import.poi.raw_files import (
    append_features_jsonl,
    iter_features_jsonl,
    prepare_poi_raw_files,
    write_raw_response_file,
)
from data2001.task2_import.records import ArcGISFeature, PoiRecord, poi_records_to_db_rows


def _report_bbox_progress(
    reporter: ProgressReporter | None,
    settings: Settings,
    current: int,
    total: int,
    source_name: str,
) -> None:
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
    return (
        f"req={current}/{total} "
        f"pages={request_pages} "
        f"responses={response_count} "
        f"features={raw_feature_count} "
        f"sa2={source_name}"
    )


def _write_poi_batch(engine: Engine, settings: Settings, batch: list[PoiRecord]) -> None:
    upsert_poi_records(
        engine,
        settings.database.schema_name,
        poi_records_to_db_rows(batch),
        settings.spatial.database_srid,
    )


def _clean_and_write_features(
    engine: Engine,
    settings: Settings,
    features: Iterable[ArcGISFeature],
) -> int:
    clean_count = 0
    batch: list[PoiRecord] = []
    seen_objectids: set[int] = set()
    for feature in features:
        record = clean_poi_feature(settings, feature)
        if record is None:
            continue
        if record.objectid in seen_objectids:
            continue
        seen_objectids.add(record.objectid)
        batch.append(record)
        clean_count += 1
        if len(batch) >= settings.task2_import.clean_batch_size:
            _write_poi_batch(engine, settings, batch)
            batch = []
    _write_poi_batch(engine, settings, batch)
    return clean_count


def _assign_if_needed(engine: Engine, settings: Settings, clean_and_assign: bool) -> None:
    if clean_and_assign:
        assign_poi_to_sa2(engine, settings.database.schema_name, settings.spatial.assignment_method)


def run_poi_import(
    engine: Engine,
    settings: Settings,
    *,
    clean_and_assign: bool = True,
    reporter: ProgressReporter | None = None,
) -> StepSummary:
    client = create_arcgis_client(settings)
    validate_metadata(client, settings, ["poi", "sa2"])
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
        alive_bar(total_requests, title="import-poi", bar="smooth")
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
        clean_count = _clean_and_write_features(engine, settings, iter_features_jsonl(settings))
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
