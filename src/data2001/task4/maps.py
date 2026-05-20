"""Notebook、report 和 Dash 共用的 Plotly 地图构建函数."""
from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

EXCLUDED_FILL_COLOR = "rgba(107, 114, 128, 0.26)"
EXCLUDED_LINE_COLOR = "rgba(75, 85, 99, 0.55)"


def _score_geojson(scores_df: pd.DataFrame) -> dict:
    """把带 geometry 的 SA2 score DataFrame 转成 Plotly 可用的 GeoJSON."""
    features = []
    for row in scores_df.to_dict("records"):
        geometry = row["geometry"]
        if isinstance(geometry, str):
            geometry = json.loads(geometry)
        features.append(
            {
                "type": "Feature",
                "id": row["sa2_code"],
                "properties": {
                    "sa2_code": row["sa2_code"],
                    "sa2_name": row["sa2_name"],
                    "sa4_name": row["sa4_name"],
                },
                "geometry": geometry,
            }
        )
    return {"type": "FeatureCollection", "features": features}


def _split_scored_and_excluded(scores_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split map rows into scored areas and neutral excluded background areas."""
    if scores_df.empty:
        return scores_df, scores_df

    score = pd.to_numeric(scores_df["score_100"], errors="coerce")
    if "is_excluded" in scores_df.columns:
        excluded_mask = scores_df["is_excluded"].fillna(False).astype(bool) | score.isna()
    else:
        excluded_mask = score.isna()

    excluded = scores_df.loc[excluded_mask].copy()
    scored = scores_df.loc[~excluded_mask].copy()
    return scored, excluded


def _excluded_hover_data(excluded_df: pd.DataFrame) -> list[list[object]]:
    """Return compact hover rows for excluded SA2 map areas."""
    reason = (
        excluded_df["exclusion_reason"]
        if "exclusion_reason" in excluded_df.columns
        else pd.Series("Excluded from score", index=excluded_df.index)
    )
    return [
        [
            row["sa2_name"],
            row["sa4_name"],
            row["population"],
            row["poi_count"],
            row["reason"] or "Excluded from score",
        ]
        for row in pd.DataFrame(
            {
                "sa2_name": excluded_df["sa2_name"],
                "sa4_name": excluded_df["sa4_name"],
                "population": excluded_df["population"],
                "poi_count": excluded_df["poi_count"],
                "reason": reason,
            }
        ).to_dict("records")
    ]


def _excluded_sa2_trace(excluded_df: pd.DataFrame) -> go.Choroplethmap:
    """Build the grey/transparent background layer for SA2s excluded from scoring."""
    return go.Choroplethmap(
        geojson=_score_geojson(excluded_df),
        locations=excluded_df["sa2_code"],
        featureidkey="properties.sa2_code",
        z=[0] * len(excluded_df),
        colorscale=[[0, EXCLUDED_FILL_COLOR], [1, EXCLUDED_FILL_COLOR]],
        marker={"line": {"width": 0.7, "color": EXCLUDED_LINE_COLOR}},
        showscale=False,
        showlegend=False,
        name="Excluded from score",
        customdata=_excluded_hover_data(excluded_df),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "SA4=%{customdata[1]}<br>"
            "Population=%{customdata[2]}<br>"
            "POI count=%{customdata[3]}<br>"
            "%{customdata[4]}"
            "<extra></extra>"
        ),
    )


def _prepend_excluded_layer(fig: go.Figure, excluded_df: pd.DataFrame) -> go.Figure:
    """Draw excluded SA2s under the scored choropleth layer."""
    if excluded_df.empty:
        return fig
    excluded_trace = _excluded_sa2_trace(excluded_df)
    return go.Figure(data=[excluded_trace, *fig.data], layout=fig.layout)


def build_score_choropleth_map(scores_df: pd.DataFrame) -> go.Figure:
    """构建 SA2 score choropleth 地图."""
    scored_df, excluded_df = _split_scored_and_excluded(scores_df)
    geojson = _score_geojson(scored_df)
    fig = px.choropleth_map(
        scored_df,
        geojson=geojson,
        locations="sa2_code",
        featureidkey="properties.sa2_code",
        color="score_100",
        hover_name="sa2_name",
        hover_data={
            "sa4_name": True,
            "population": True,
            "poi_count": True,
            "z_poi": ":.3f",
            "score_100": ":.2f",
            "sa2_code": False,
        },
        color_continuous_scale="Viridis",
        labels={
            "score_100": "Score (0-100)",
            "z_poi": "zPOI",
            "poi_count": "POI count",
            "population": "Population",
            "sa4_name": "SA4",
        },
        map_style="carto-positron",
        zoom=9,
        center={"lat": -33.86, "lon": 151.1},
        opacity=0.72,
        title="SA2 well-resourced score map",
    )
    fig = _prepend_excluded_layer(fig, excluded_df)
    fig.update_layout(
        coloraxis_colorbar={"title": "Score (0-100)"},
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
    )
    return fig


def build_poi_density_choropleth_map(scores_df: pd.DataFrame) -> go.Figure:
    """构建按人口调整后的 SA2 POI 密度 choropleth 地图."""
    data = scores_df.copy()
    population = pd.to_numeric(data["population"], errors="coerce")
    poi_count = pd.to_numeric(data["poi_count"], errors="coerce")
    data["poi_per_1000"] = (poi_count / population.where(population > 0)) * 1000
    scored_df, excluded_df = _split_scored_and_excluded(data)

    geojson = _score_geojson(scored_df)
    fig = px.choropleth_map(
        scored_df,
        geojson=geojson,
        locations="sa2_code",
        featureidkey="properties.sa2_code",
        color="poi_per_1000",
        hover_name="sa2_name",
        hover_data={
            "sa4_name": True,
            "population": True,
            "poi_count": True,
            "poi_per_1000": ":.2f",
            "score_100": ":.2f",
            "sa2_code": False,
        },
        color_continuous_scale="Plasma",
        labels={
            "poi_per_1000": "POI per 1,000 people",
            "poi_count": "POI count",
            "population": "Population",
            "score_100": "Score (0-100)",
            "sa4_name": "SA4",
        },
        map_style="carto-positron",
        zoom=9,
        center={"lat": -33.86, "lon": 151.1},
        opacity=0.72,
        title="Population-adjusted POI density by SA2",
    )
    fig = _prepend_excluded_layer(fig, excluded_df)
    fig.update_layout(
        coloraxis_colorbar={"title": "POI per 1,000 people"},
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
    )
    return fig


def build_poi_point_scatter_map(poi_df: pd.DataFrame) -> go.Figure:
    """构建 POI 点位 scatter map."""
    fig = px.scatter_map(
        poi_df,
        lat="latitude",
        lon="longitude",
        color="poigroup_name",
        hover_name="poiname",
        hover_data={
            "poitype": True,
            "objectid": True,
            "latitude": ":.5f",
            "longitude": ":.5f",
        },
        map_style="carto-positron",
        zoom=9,
        center={"lat": -33.86, "lon": 151.1},
        title="POI point locations",
    )
    fig.update_traces(marker={"size": 3.5, "opacity": 0.6}) # 调整点的大小和透明度
    fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})
    return fig
