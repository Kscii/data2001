"""Report PNG 导出入口, 复用 notebook 和 Dash 使用的 Plotly 图表构建函数."""
from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
from sqlalchemy import Engine

from data2001_assignment.common.paths import resolve_project_path
from data2001_assignment.config import Settings
from data2001_assignment.visualisation.figures import (
    build_bottom_sa2_bar,
    build_poi_group_distribution,
    build_score_histogram,
    build_score_income_scatter,
    build_top_sa2_bar,
)
from data2001_assignment.visualisation.maps import (
    build_poi_point_scatter_map,
    build_score_choropleth_map,
)
from data2001_assignment.visualisation.queries import (
    load_poi_group_counts,
    load_poi_points,
    load_sa2_scores,
    load_score_income,
)


def write_png(fig: go.Figure, path: Path, settings: Settings) -> None:
    """把单个 Plotly figure 导出为 PNG 文件."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(
        str(path),
        format=settings.figures.format,
        width=settings.figures.width,
        height=settings.figures.height,
        scale=settings.figures.scale,
    )


def generate_report_figures(engine: Engine, settings: Settings) -> dict[str, Path]:
    """查询数据库并生成 report 需要的所有 PNG 图表."""
    figures_dir = resolve_project_path(settings.outputs.figures_dir)
    scores = load_sa2_scores(
        engine,
        settings.database.schema_name,
        score_version=settings.scoring.score_version,
        score_universe=settings.scoring.score_universe,
    )
    group_counts = load_poi_group_counts(engine, settings.database.schema_name)
    score_income = load_score_income(
        engine,
        settings.database.schema_name,
        score_version=settings.scoring.score_version,
        score_universe=settings.scoring.score_universe,
    )
    poi_points = load_poi_points(engine, settings.database.schema_name)

    figures: dict[str, go.Figure] = {
        "score_histogram.png": build_score_histogram(scores, nbins=settings.figures.score_histogram_nbins),
        "top_sa2_score.png": build_top_sa2_bar(scores, n=settings.figures.top_n),
        "bottom_sa2_score.png": build_bottom_sa2_bar(scores, n=settings.figures.top_n),
        "poi_group_distribution.png": build_poi_group_distribution(group_counts),
        "score_income_correlation.png": build_score_income_scatter(score_income),
        "sa2_score_choropleth.png": build_score_choropleth_map(scores),
        "poi_point_scatter.png": build_poi_point_scatter_map(poi_points),
    }
    output_paths: dict[str, Path] = {}
    for file_name, figure in figures.items():
        output_path = figures_dir / file_name
        write_png(figure, output_path, settings)
        output_paths[file_name] = output_path
    return output_paths
