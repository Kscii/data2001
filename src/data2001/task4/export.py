"""Report PNG 导出入口, 复用 notebook 和 Dash 使用的 Plotly 图表构建函数."""
from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
from sqlalchemy import Engine

from data2001.common.paths import resolve_project_path
from data2001.config import Settings
from data2001.task4.charts import (
    build_bottom_sa2_bar,
    build_poi_group_distribution,
    build_score_histogram,
    build_score_income_scatter,
    build_top_sa2_bar,
)
from data2001.task4.maps import (
    build_poi_point_scatter_map,
    build_score_choropleth_map,
)
from data2001.task4.queries import (
    select_poi_group_counts,
    select_poi_points,
    select_sa2_scores,
    select_score_income,
)
from data2001.task4.records import (
    poi_group_count_views_to_dataframe,
    poi_point_views_to_dataframe,
    sa2_score_views_to_dataframe,
    score_income_views_to_dataframe,
)


def write_png(fig: go.Figure, path: Path, settings: Settings) -> None:
    """把单个 Plotly figure 导出为 PNG 文件."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(
        str(path),
        format=settings.charts.format,
        width=settings.charts.width,
        height=settings.charts.height,
        scale=settings.charts.scale,
    )


def export_report_charts(engine: Engine, settings: Settings) -> dict[str, Path]:
    """查询数据库并生成 report 需要的所有 PNG 图表."""
    charts_dir = resolve_project_path(settings.outputs.charts_dir)
    scores = sa2_score_views_to_dataframe(
        select_sa2_scores(
            engine,
            settings.database.schema_name,
            score_version=settings.task3_score.score_version,
            score_universe=settings.task3_score.score_universe,
        )
    )
    group_counts = poi_group_count_views_to_dataframe(
        select_poi_group_counts(engine, settings.database.schema_name)
    )
    score_income = score_income_views_to_dataframe(
        select_score_income(
            engine,
            settings.database.schema_name,
            score_version=settings.task3_score.score_version,
            score_universe=settings.task3_score.score_universe,
        )
    )
    poi_points = poi_point_views_to_dataframe(
        select_poi_points(engine, settings.database.schema_name)
    )

    charts: dict[str, go.Figure] = {
        "score_histogram.png": build_score_histogram(scores, nbins=settings.charts.score_histogram_nbins),
        "top_sa2_score.png": build_top_sa2_bar(scores, n=settings.charts.top_n),
        "bottom_sa2_score.png": build_bottom_sa2_bar(scores, n=settings.charts.top_n),
        "poi_group_distribution.png": build_poi_group_distribution(group_counts),
        "score_income_correlation.png": build_score_income_scatter(score_income),
        "sa2_score_choropleth.png": build_score_choropleth_map(scores),
        "poi_point_scatter.png": build_poi_point_scatter_map(poi_points),
    }
    output_paths: dict[str, Path] = {}
    for file_name, chart in charts.items():
        output_path = charts_dir / file_name
        write_png(chart, output_path, settings)
        output_paths[file_name] = output_path
    return output_paths
