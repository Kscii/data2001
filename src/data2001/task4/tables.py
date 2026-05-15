"""Notebook 和 Dash 共用的表格数据整理函数."""
from __future__ import annotations

from typing import Any, cast

import pandas as pd


def build_top_bottom_table(scores_df: pd.DataFrame, *, n: int) -> pd.DataFrame:
    """整理 Top N 和 Bottom N SA2 score 表格."""
    columns = ["sa2_code", "sa2_name", "sa4_name", "poi_count", "score_100", "population"]
    top = scores_df.nlargest(n, "score_100").copy()
    top["rank_group"] = "top"
    bottom = scores_df.nsmallest(n, "score_100").copy()
    bottom["rank_group"] = "bottom"
    return cast(pd.DataFrame, pd.concat([top, bottom], ignore_index=True).loc[:, ["rank_group", *columns]])


def build_sa4_summary_table(scores_df: pd.DataFrame, poi_df: pd.DataFrame) -> pd.DataFrame:
    """整理 SA4 层面的 score 和 POI 汇总表."""
    columns = [
        "sa4_name",
        "sa2_count",
        "total_poi",
        "mean_score_100",
        "median_score_100",
        "highest_score_sa2",
        "highest_score_100",
        "lowest_score_sa2",
        "lowest_score_100",
    ]
    if scores_df.empty:
        return pd.DataFrame(columns=columns)

    score_rows = scores_df.dropna(subset=["sa4_name"]).copy()
    if score_rows.empty:
        return pd.DataFrame(columns=columns)

    summary = cast(pd.DataFrame, (
        score_rows.groupby("sa4_name", dropna=False)
        .agg(
            sa2_count=("sa2_code", "nunique"),
            mean_score_100=("score_100", "mean"),
            median_score_100=("score_100", "median"),
        )
        .reset_index()
    ))

    if poi_df.empty:
        poi_counts = pd.DataFrame({"sa4_name": summary["sa4_name"], "total_poi": 0})
    else:
        poi_count_series = cast(Any, poi_df.dropna(subset=["sa4_name"]).groupby("sa4_name", dropna=False).size())
        poi_counts = cast(pd.DataFrame, poi_count_series.reset_index(name="total_poi"))
    summary = summary.merge(poi_counts, on="sa4_name", how="left")
    summary["total_poi"] = summary["total_poi"].fillna(0).astype(int)

    highest = (
        score_rows.sort_values(by=["sa4_name", "score_100"], ascending=[True, False])
        .drop_duplicates("sa4_name")
        .loc[:, ["sa4_name", "sa2_name", "score_100"]]
        .rename(columns={"sa2_name": "highest_score_sa2", "score_100": "highest_score_100"})
    )
    lowest = (
        score_rows.sort_values(by=["sa4_name", "score_100"], ascending=[True, True])
        .drop_duplicates("sa4_name")
        .loc[:, ["sa4_name", "sa2_name", "score_100"]]
        .rename(columns={"sa2_name": "lowest_score_sa2", "score_100": "lowest_score_100"})
    )
    result = cast(pd.DataFrame, summary.merge(highest, on="sa4_name", how="left").merge(lowest, on="sa4_name", how="left"))
    for column in ["mean_score_100", "median_score_100", "highest_score_100", "lowest_score_100"]:
        result[column] = result[column].round(2)
    return cast(pd.DataFrame, result.loc[:, columns].sort_values(by="mean_score_100", ascending=False))
