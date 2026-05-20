"""Task 3 score 公式：基于 POI count 的 z-score 和 sigmoid 变换."""
from __future__ import annotations

import math
from typing import Any, cast

import pandas as pd

from data2001.task3_score.records import (
    Sa2ScoreRecord,
    ScoreInputRecord,
    score_input_records_to_dataframe,
    score_records_from_dataframe,
)


def sigmoid(value: float) -> float:
    """计算 sigmoid, 用于把 z-score 压到 0-1 区间."""
    return 1 / (1 + math.exp(-value))


def compute_scores(
    score_inputs: list[ScoreInputRecord],
    *,
    score_version: str,
    score_universe: str,
    min_population: int,
    output_scale: int,
) -> list[Sa2ScoreRecord]:
    """根据每个 SA2 的 POI 数量计算 baseline score."""
    sa2_counts = score_input_records_to_dataframe(score_inputs)
    required = {"sa2_code", "poi_count", "population"}
    missing = required.difference(sa2_counts.columns)
    if missing:
        raise ValueError(f"score 输入缺少字段: {sorted(missing)}")

    df = sa2_counts.copy()
    population = cast(pd.Series, pd.to_numeric(df["population"], errors="coerce"))
    population_mask = cast(pd.Series, population >= min_population)
    df = cast(pd.DataFrame, df.loc[population_mask].copy())

    poi_count = cast(pd.Series, pd.to_numeric(df["poi_count"], errors="coerce"))
    mean = float(cast(Any, poi_count.mean()))
    std = float(cast(Any, poi_count.std(ddof=0)))
    if not std or pd.isna(std):
        df["z_poi"] = 0.0
    else:
        df["z_poi"] = (poi_count - mean) / std

    df["score_version"] = score_version
    df["score_universe"] = score_universe
    df["mean_poi_count"] = mean
    df["std_poi_count"] = std
    df["score_raw"] = cast(pd.Series, df["z_poi"]).map(sigmoid)
    df["score_100"] = df["score_raw"] * output_scale
    return score_records_from_dataframe(df)
