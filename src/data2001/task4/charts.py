from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_score_histogram(scores_df: pd.DataFrame, *, nbins: int) -> go.Figure:
    fig = px.histogram(
        scores_df,
        x="score_100",
        nbins=nbins,
        labels={"score_100": "Well-resourced score (0-100)", "count": "SA2 count"},
        title="Distribution of SA2 well-resourced scores",
    )
    fig.update_layout(bargap=0.08)
    return fig


def build_top_sa2_bar(scores_df: pd.DataFrame, *, n: int) -> go.Figure:
    data = (
        scores_df.sort_values(
            ["score_100", "sa4_name", "sa2_name"],
            ascending=[False, True, True],
        )
        .head(n)
        .sort_values(["score_100", "sa4_name", "sa2_name"], ascending=[True, False, False])
    )
    fig = px.bar(
        data,
        x="score_100",
        y="sa2_name",
        orientation="h",
        color="sa4_name",
        labels={"score_100": "Score (0-100)", "sa2_name": "SA2", "sa4_name": "SA4"},
        title=f"Top {n} SA2s by score",
    )
    fig.update_xaxes(range=[0, 100])
    return fig


def build_bottom_sa2_bar(scores_df: pd.DataFrame, *, n: int) -> go.Figure:
    data = (
        scores_df.sort_values(
            ["score_100", "sa4_name", "sa2_name"],
            ascending=[True, True, True],
        )
        .head(n)
        .sort_values(["score_100", "sa4_name", "sa2_name"], ascending=[False, False, False])
    )
    fig = px.bar(
        data,
        x="score_100",
        y="sa2_name",
        orientation="h",
        color="sa4_name",
        labels={"score_100": "Score (0-100)", "sa2_name": "SA2", "sa4_name": "SA4"},
        title=f"Bottom {n} SA2s by score",
    )
    fig.update_xaxes(range=[0, 100])
    return fig


def build_poi_group_distribution(group_df: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        group_df.sort_values("poi_count"),
        x="poi_count",
        y="poigroup_name",
        orientation="h",
        labels={"poi_count": "POI count", "poigroup_name": "POI group"},
        title="POI group distribution",
    )
    return fig


def build_sa4_score_boxplot(scores_df: pd.DataFrame) -> go.Figure:
    fig = px.box(
        scores_df,
        x="sa4_name",
        y="score_100",
        points="all",
        labels={"sa4_name": "SA4", "score_100": "Score (0-100)"},
        title="SA2 score distribution by SA4",
    )
    fig.update_layout(xaxis_tickangle=-30)
    return fig


def build_poi_group_by_sa4_bar(poi_df: pd.DataFrame) -> go.Figure:
    grouped = cast(Any, poi_df.groupby(["sa4_name", "poigroup_name"], dropna=False).size())
    grouped = cast(pd.DataFrame, grouped.reset_index(name="poi_count"))
    grouped = cast(pd.DataFrame, grouped.sort_values(by=["sa4_name", "poigroup_name"]))
    fig = px.bar(
        grouped,
        x="sa4_name",
        y="poi_count",
        color="poigroup_name",
        labels={"sa4_name": "SA4", "poi_count": "POI count", "poigroup_name": "POI group"},
        title="POI group composition by SA4",
    )
    fig.update_layout(barmode="stack", xaxis_tickangle=-30)
    return fig


def build_score_income_scatter(score_income_df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        score_income_df,
        x="median_income_2022_23",
        y="score_100",
        size="poi_count",
        color="sa4_name",
        hover_name="sa2_name",
        labels={
            "median_income_2022_23": "Median income 2022-23 ($)",
            "score_100": "Score (0-100)",
            "poi_count": "POI count",
            "sa4_name": "SA4",
        },
        title="Well-resourced score vs median income",
    )
    trend_data = score_income_df.dropna(subset=["median_income_2022_23", "score_100"])
    if len(trend_data) >= 2 and trend_data["median_income_2022_23"].nunique() >= 2:
        x = trend_data["median_income_2022_23"].astype(float)
        y = trend_data["score_100"].astype(float)
        slope, intercept = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = slope * x_line + intercept
        fig.add_trace(
            go.Scatter(
                x=x_line,
                y=y_line,
                mode="lines",
                name="Linear trend",
                line={"color": "rgba(17, 24, 39, 0.65)", "width": 1.5, "dash": "dash"},
            )
        )
    return fig
