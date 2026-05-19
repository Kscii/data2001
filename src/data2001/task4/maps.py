"""Notebook、report 和 Dash 共用的 Plotly 地图构建函数."""
from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


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


def build_score_choropleth_map(scores_df: pd.DataFrame) -> go.Figure:
    """构建 SA2 score choropleth 地图."""
    geojson = _score_geojson(scores_df)
    fig = px.choropleth_map(
        scores_df,
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
        zoom=8,
        center={"lat": -33.86, "lon": 151.1},
        opacity=0.72,
        title="SA2 well-resourced score map",
    )
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

    geojson = _score_geojson(data)
    fig = px.choropleth_map(
        data,
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
        zoom=8,
        center={"lat": -33.86, "lon": 151.1},
        opacity=0.72,
        title="Population-adjusted POI density by SA2",
    )
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
        zoom=8,
        center={"lat": -33.86, "lon": 151.1},
        title="POI point locations",
    )
    fig.update_traces(marker={"size": 3.5, "opacity": 0.6}) # 调整点的大小和透明度
    fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})
    return fig
