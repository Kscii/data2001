"""Notebook、report 和 Dash 共用的 Plotly 地图构建函数."""
from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_score_choropleth_map(scores_df: pd.DataFrame) -> go.Figure:
    """构建 SA2 score choropleth 地图."""
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

    geojson = {"type": "FeatureCollection", "features": features}
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
