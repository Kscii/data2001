"""Task 3 score 公式：基于 POI count 的 z-score 和 sigmoid 变换."""
from __future__ import annotations

import math

import pandas as pd


def sigmoid(value: float) -> float:
    """计算 sigmoid, 用于把 z-score 压到 0-1 区间."""
    return 1 / (1 + math.exp(-value))


def compute_scores(
    sa2_counts: pd.DataFrame,
    *,
    score_version: str,
    score_universe: str,
    min_population: int,
    output_scale: int,
) -> pd.DataFrame:
    """根据每个 SA2 的 POI 数量计算 baseline score."""
    required = {"sa2_code", "poi_count", "population"}
    missing = required.difference(sa2_counts.columns)
    if missing:
        raise ValueError(f"score 输入缺少字段: {sorted(missing)}")

    df = sa2_counts.copy()
    df = df[df["population"].isna() | (df["population"] >= min_population)].copy()

    mean = float(df["poi_count"].mean())
    std = float(df["poi_count"].std(ddof=0))
    if not std or pd.isna(std):
        df["z_poi"] = 0.0
    else:
        df["z_poi"] = (df["poi_count"] - mean) / std

    df["score_version"] = score_version
    df["score_universe"] = score_universe
    df["mean_poi_count"] = mean
    df["std_poi_count"] = std
    df["score_raw"] = df["z_poi"].map(sigmoid)
    df["score_100"] = df["score_raw"] * output_scale
    return df
