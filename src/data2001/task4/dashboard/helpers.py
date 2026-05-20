from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, cast

import pandas as pd
import plotly.graph_objects as go
from dash import html
from dash.dash_table.DataTable import DataTable
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from data2001.config import Settings
from data2001.task4.queries import load_poi_points, load_sa2_scores

T = TypeVar("T")


def empty_figure(title: str, message: str = "No data available") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
            }
        ],
    )
    return fig


def as_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def safe_load(default: T, loader: Callable[[], T]) -> T:
    try:
        return loader()
    except SQLAlchemyError:
        return default


def filter_common(df: pd.DataFrame, *, sa4_names: list[str], sa2_codes: list[str]) -> pd.DataFrame:
    if df.empty:
        return df
    result = df
    if sa4_names and "sa4_name" in result.columns:
        sa4_mask = cast(pd.Series, result["sa4_name"]).isin(sa4_names)
        result = cast(pd.DataFrame, result.loc[sa4_mask])
    if sa2_codes and "sa2_code" in result.columns:
        sa2_mask = cast(pd.Series, result["sa2_code"]).isin(sa2_codes)
        result = cast(pd.DataFrame, result.loc[sa2_mask])
    return result


def filter_poi(
    poi_df: pd.DataFrame,
    *,
    sa4_names: list[str],
    sa2_codes: list[str],
    poi_groups: list[str],
) -> pd.DataFrame:
    result = filter_common(poi_df, sa4_names=sa4_names, sa2_codes=sa2_codes)
    if not result.empty and poi_groups and "poigroup_name" in result.columns:
        group_mask = cast(pd.Series, result["poigroup_name"]).isin(poi_groups)
        result = cast(pd.DataFrame, result.loc[group_mask])
    return result


def poi_group_counts(poi_df: pd.DataFrame) -> pd.DataFrame:
    if poi_df.empty:
        return pd.DataFrame(columns=["poigroup_name", "poigroup_code", "poi_count"])
    counts = cast(Any, poi_df.groupby(["poigroup_name", "poigroup_code"], dropna=False).size())
    counts = counts.reset_index(name="poi_count")
    counts = counts.sort_values(by=["poi_count", "poigroup_name"], ascending=[False, True])
    return cast(pd.DataFrame, counts)


def table_columns(df: pd.DataFrame) -> list[dict[str, str]]:
    return [{"name": column, "id": column} for column in df.columns]


def table_records(df: pd.DataFrame, *, max_rows: int) -> list[dict[str, Any]]:
    if df.empty:
        return []
    return cast(list[dict[str, Any]], df.head(max_rows).to_dict("records"))


def score_table(scores: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "sa2_code",
        "sa2_name",
        "sa4_name",
        "population",
        "poi_count",
        "z_poi",
        "score_100",
    ]
    if scores.empty:
        return pd.DataFrame(columns=columns)
    result = cast(pd.DataFrame, scores.loc[:, columns].copy())
    result["score_100"] = cast(pd.Series, result["score_100"]).round(2)
    result["z_poi"] = cast(pd.Series, result["z_poi"]).round(3)
    return cast(pd.DataFrame, result.sort_values(by="score_100", ascending=False))


def poi_summary_table(poi_df: pd.DataFrame) -> pd.DataFrame:
    columns = ["sa4_name", "sa2_name", "poigroup_name", "poi_count"]
    if poi_df.empty:
        return pd.DataFrame(columns=columns)
    summary = cast(Any, poi_df.groupby(["sa4_name", "sa2_name", "poigroup_name"], dropna=False).size())
    summary = summary.reset_index(name="poi_count")
    summary = summary.sort_values(by="poi_count", ascending=False)
    return cast(pd.DataFrame, summary)


def correlation_summary(correlation: pd.DataFrame) -> str:
    if correlation.empty:
        return "No correlation test result is available for the current score configuration."
    significant_mask = cast(pd.Series, correlation["is_significant"]).astype(bool)
    significant = cast(pd.DataFrame, correlation.loc[significant_mask])
    if significant.empty:
        return "No statistically significant relationship found between score and median income."
    methods = ", ".join(cast(pd.Series, significant["method"]).astype(str).str.title().tolist())
    return f"Statistically significant relationship found for: {methods}."


def kpi_cards(
    scores: pd.DataFrame,
    score_areas: pd.DataFrame,
    poi_df: pd.DataFrame,
    score_income: pd.DataFrame,
) -> list[html.Div]:
    values = [
        ("SA2 areas", len(score_areas)),
        ("Assigned POI", len(poi_df)),
        (
            "Mean score (scored SA2)",
            f"{float(cast(Any, cast(pd.Series, scores['score_100']).mean())):.1f}" if not scores.empty else "n/a",
        ),
        ("Income sample (scored)", len(score_income)),
    ]
    return [
        html.Div(
            [html.Div(label, className="kpi-label"), html.Div(str(value), className="kpi-value")],
            className="kpi-card",
        )
        for label, value in values
    ]


def data_table(
    table_id: str,
    *,
    data: list[dict[str, Any]] | None = None,
    columns: list[dict[str, str]] | None = None,
    page_size: int,
) -> Any:
    return DataTable(
        id=table_id,
        data=cast(Any, data or []),
        columns=cast(Any, columns or []),
        page_size=page_size,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto"},
        style_cell={
            "fontFamily": "system-ui, sans-serif",
            "fontSize": 13,
            "padding": "6px",
            "textAlign": "left",
            "maxWidth": 260,
            "whiteSpace": "normal",
        },
        style_header={"fontWeight": "700", "backgroundColor": "#f3f4f6"},
    )


def dashboard_options(values: list[Any]) -> list[dict[str, Any]]:
    return [{"label": str(value), "value": value} for value in values if value is not None]


def unique_options(df: pd.DataFrame, column: str) -> list[dict[str, Any]]:
    if column not in df.columns:
        return []
    values = cast(pd.Series, df[column]).dropna().unique().tolist()
    return dashboard_options(sorted(values))


def initial_options(engine: Engine, settings: Settings) -> dict[str, list[dict[str, Any]]]:
    scores = safe_load(pd.DataFrame(), lambda: load_sa2_scores(engine, settings, include_excluded=True))
    poi = safe_load(pd.DataFrame(), lambda: load_poi_points(engine, settings, limit=settings.dashboard.poi_limit))
    return {
        "sa4": unique_options(scores, "sa4_name"),
        "sa2": unique_options(scores, "sa2_code"),
        "poi_groups": unique_options(poi, "poigroup_name"),
    }
