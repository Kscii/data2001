from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Iterator

from data2001.common.paths import resolve_project_path
from data2001.config import Settings
from data2001.task2_import.records import ArcGISFeature, ArcGISPayload


def prepare_poi_raw_files(settings: Settings) -> tuple[Path, Path]:
    response_dir = resolve_project_path(settings.outputs.raw_poi_response_dir)
    features_path = resolve_project_path(settings.outputs.raw_poi_features_jsonl)
    response_dir.mkdir(parents=True, exist_ok=True)
    features_path.parent.mkdir(parents=True, exist_ok=True)

    for path in response_dir.glob("*.json"):
        path.unlink()
    if features_path.exists():
        features_path.unlink()
    return response_dir, features_path


def write_raw_response_file(
    response_dir: Path,
    *,
    sequence: int,
    source_code: str,
    offset: int,
    request_params: dict[str, Any],
    payload: ArcGISPayload,
) -> Path:
    path = response_dir / f"response_{sequence:06d}_{source_code}_{offset}.json"
    document = {
        "request_params": request_params,
        "payload": payload,
    }
    path.write_text(json.dumps(document, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def append_features_jsonl(features_path: Path, features: Iterable[ArcGISFeature]) -> int:
    count = 0
    with features_path.open("a", encoding="utf-8") as file:
        for feature in features:
            file.write(json.dumps(feature, ensure_ascii=False, sort_keys=True))
            file.write("\n")
            count += 1
    return count


def iter_features_jsonl(settings: Settings) -> Iterator[ArcGISFeature]:
    features_path = resolve_project_path(settings.outputs.raw_poi_features_jsonl)
    if not features_path.exists():
        return
    with features_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                yield json.loads(line)
