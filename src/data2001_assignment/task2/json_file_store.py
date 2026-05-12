"""POI raw JSON 文件存储：保存分页 response, 并提供 features.jsonl 流式读写."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Iterator

from data2001_assignment.common.paths import resolve_project_path
from data2001_assignment.config import Settings


def prepare_poi_raw_files(settings: Settings) -> tuple[Path, Path]:
    """准备 file_raw 输出位置, 并清掉上一次运行留下的 raw 文件."""
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
    payload: dict[str, Any],
) -> Path:
    """保存单页 API response, 尽量保留请求参数和原始 payload."""
    path = response_dir / f"response_{sequence:06d}_{source_code}_{offset}.json"
    document = {
        "request_params": request_params,
        "payload": payload,
    }
    path.write_text(json.dumps(document, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def append_features_jsonl(features_path: Path, features: Iterable[dict[str, Any]]) -> int:
    """把 raw feature 追加成 JSONL；后续清洗可以流式读取."""
    count = 0
    with features_path.open("a", encoding="utf-8") as file:
        for feature in features:
            file.write(json.dumps(feature, ensure_ascii=False, sort_keys=True))
            file.write("\n")
            count += 1
    return count


def iter_features_jsonl(settings: Settings) -> Iterator[dict[str, Any]]:
    """逐行读取 features.jsonl, 供清洗阶段流式消费."""
    features_path = resolve_project_path(settings.outputs.raw_poi_features_jsonl)
    if not features_path.exists():
        return
    with features_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                yield json.loads(line)
