from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
from sqlalchemy import Engine

from data2001.common.paths import resolve_project_path
from data2001.config import Settings
from data2001.task4.charts import (
    build_bottom_sa2_bar,
    build_poi_group_distribution,
    build_sa4_score_boxplot,
    build_score_histogram,
    build_score_income_scatter,
    build_top_sa2_bar,
)
from data2001.task4.maps import (
    build_poi_density_choropleth_map,
    build_poi_point_scatter_map,
    build_score_choropleth_map,
)
from data2001.task4.queries import (
    load_poi_group_counts,
    load_poi_points,
    load_sa2_scores,
    load_score_income,
)


def write_png(fig: go.Figure, path: Path, settings: Settings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(
        str(path),
        format=settings.charts.format,
        width=settings.charts.width,
        height=settings.charts.height,
        scale=settings.charts.scale,
    )


def export_report_charts(engine: Engine, settings: Settings) -> dict[str, Path]:
    charts_dir = resolve_project_path(settings.outputs.charts_dir)
    scores = load_sa2_scores(engine, settings)
    score_map_areas = load_sa2_scores(engine, settings, include_excluded=True)
    group_counts = load_poi_group_counts(engine, settings)
    score_income = load_score_income(engine, settings)
    poi_points = load_poi_points(engine, settings)

    charts: dict[str, go.Figure] = {
        "score_histogram.png": build_score_histogram(scores, nbins=settings.charts.score_histogram_nbins),
        "top_sa2_score.png": build_top_sa2_bar(scores, n=settings.charts.top_n),
        "bottom_sa2_score.png": build_bottom_sa2_bar(scores, n=settings.charts.top_n),
        "sa4_score_boxplot.png": build_sa4_score_boxplot(scores),
        "poi_group_distribution.png": build_poi_group_distribution(group_counts),
        "score_income_correlation.png": build_score_income_scatter(score_income),
        "sa2_score_choropleth.png": build_score_choropleth_map(score_map_areas),
        "poi_density_choropleth.png": build_poi_density_choropleth_map(score_map_areas),
        "poi_point_scatter.png": build_poi_point_scatter_map(poi_points),
    }
    output_paths: dict[str, Path] = {}
    for file_name, chart in charts.items():
        output_path = charts_dir / file_name
        write_png(chart, output_path, settings)
        output_paths[file_name] = output_path
    return output_paths
