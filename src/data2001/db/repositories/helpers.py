"""Shared helpers for database repository modules."""
from __future__ import annotations

import json
import math
from typing import Any

BUSINESS_TABLES = [
    "score_income_correlation",
    "sa2_score",
    "sa2_income",
    "sa2_poi",
    "poi_clean",
    "sa2",
    "sa4",
]


def to_json(value: Any) -> str:
    """Serialize a Python value as stable JSON for PostGIS."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def none_if_nan(value: Any) -> Any:
    """Convert NaN values to None before database writes."""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value

