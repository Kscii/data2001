"""Dashboard callbacks, 负责根据筛选条件查询数据并生成当前 tab 内容."""
from __future__ import annotations

import pandas as pd
from dash import Dash, Input, Output, html
from dash.dcc.Graph import Graph
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from data2001.config import Settings
from data2001.task4_visuals.charts import (
    build_bottom_sa2_bar,
    build_poi_group_distribution,
    build_poi_group_by_sa4_bar,
    build_sa4_score_boxplot,
    build_score_histogram,
    build_score_income_scatter,
    build_top_sa2_bar,
)
from data2001.task4_visuals.dashboard.helpers import (
    as_list,
    correlation_summary,
    data_table,
    empty_figure,
    filter_common,
    filter_poi,
    kpi_cards,
    poi_group_counts,
    poi_summary_table,
    score_table,
    table_columns,
    table_records,
)
from data2001.task4_visuals.maps import (
    build_poi_point_scatter_map,
    build_score_choropleth_map,
)
from data2001.task4_visuals.queries import (
    select_correlation_results,
    select_poi_points,
    select_sa2_scores,
    select_score_income,
)
from data2001.task4_visuals.records import (
    correlation_result_views_to_dataframe,
    poi_point_views_to_dataframe,
    sa2_score_views_to_dataframe,
    score_income_views_to_dataframe,
)
from data2001.task4_visuals.tables import build_sa4_summary_table


def register_dashboard_callbacks(app: Dash, engine: Engine, settings: Settings) -> None:
    """把 dashboard callback 注册到 Dash app."""
    schema = settings.database.schema_name

    @app.callback(
        Output("tab-content", "children"),
        Output("kpi-row", "children"),
        Input("main-tabs", "value"),
        Input("sa4-filter", "value"),
        Input("sa2-filter", "value"),
        Input("poi-group-filter", "value"),
        Input("top-n", "value"),
    )
    def render_tab(tab: str, sa4_value, sa2_value, group_value, top_n):
        """根据当前筛选器和 tab 查询数据库并返回图表、表格和 KPI."""
        sa4_names = [str(value) for value in as_list(sa4_value)]
        sa2_codes = [str(value) for value in as_list(sa2_value)]
        poi_groups = [str(value) for value in as_list(group_value)]
        n = max(int(top_n or settings.dashboard.default_top_n), 1)
        try:
            scores = sa2_score_views_to_dataframe(
                select_sa2_scores(
                    engine,
                    schema,
                    score_version=settings.task3_score.score_version,
                    score_universe=settings.task3_score.score_universe,
                )
            )
            poi = poi_point_views_to_dataframe(
                select_poi_points(engine, schema, limit=settings.dashboard.poi_limit)
            )
            score_income = score_income_views_to_dataframe(
                select_score_income(
                    engine,
                    schema,
                    score_version=settings.task3_score.score_version,
                    score_universe=settings.task3_score.score_universe,
                )
            )
            correlation = correlation_result_views_to_dataframe(
                select_correlation_results(
                    engine,
                    schema,
                    score_version=settings.task3_score.score_version,
                    score_universe=settings.task3_score.score_universe,
                )
            )
        except SQLAlchemyError as exc:
            message = html.Div(f"Database query failed: {exc}", className="panel")
            return message, kpi_cards(pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

        scores = filter_common(scores, sa4_names=sa4_names, sa2_codes=sa2_codes)
        poi = filter_poi(poi, sa4_names=sa4_names, sa2_codes=sa2_codes, poi_groups=poi_groups)
        score_income = filter_common(score_income, sa4_names=sa4_names, sa2_codes=sa2_codes)
        kpis = kpi_cards(scores, poi, score_income)

        score_histogram = (
            build_score_histogram(scores, nbins=settings.charts.score_histogram_nbins)
            if not scores.empty
            else empty_figure("Distribution of SA2 well-resourced scores")
        )
        top_bar = build_top_sa2_bar(scores, n=n) if not scores.empty else empty_figure(f"Top {n} SA2s by score")
        bottom_bar = (
            build_bottom_sa2_bar(scores, n=n)
            if not scores.empty
            else empty_figure(f"Bottom {n} SA2s by score")
        )
        sa4_boxplot = (
            build_sa4_score_boxplot(scores)
            if not scores.empty
            else empty_figure("SA2 score distribution by SA4")
        )
        score_map = (
            build_score_choropleth_map(scores)
            if not scores.empty
            else empty_figure("SA2 well-resourced score map")
        )
        poi_map = (
            build_poi_point_scatter_map(poi)
            if not poi.empty
            else empty_figure("POI point locations")
        )
        group_counts = poi_group_counts(poi)
        group_chart = (
            build_poi_group_distribution(group_counts)
            if not group_counts.empty
            else empty_figure("POI group distribution")
        )
        group_by_sa4_chart = (
            build_poi_group_by_sa4_bar(poi)
            if not poi.empty
            else empty_figure("POI group composition by SA4")
        )
        income_chart = (
            build_score_income_scatter(score_income)
            if not score_income.empty
            else empty_figure("Well-resourced score vs median income")
        )

        if tab == "overview":
            content = html.Div(
                [
                    html.Div(
                        [
                            html.Div(Graph(figure=score_histogram), className="panel"),
                            html.Div(Graph(figure=sa4_boxplot), className="panel"),
                        ],
                        className="grid-2",
                    ),
                    html.Div(
                        [
                            html.Div(Graph(figure=top_bar), className="panel"),
                            html.Div(Graph(figure=bottom_bar), className="panel"),
                        ],
                        className="grid-2",
                    ),
                ]
            )
        elif tab == "score-map":
            content = html.Div(Graph(figure=score_map, className="map-graph"), className="panel")
        elif tab == "poi-map":
            content = html.Div(
                [
                    html.Div(Graph(figure=poi_map, className="map-graph"), className="panel"),
                    html.Div(
                        [
                            html.Div(Graph(figure=group_chart), className="panel"),
                            html.Div(Graph(figure=group_by_sa4_chart), className="panel"),
                        ],
                        className="grid-2",
                    ),
                ]
            )
        elif tab == "income":
            corr_table = correlation.copy()
            if not corr_table.empty:
                corr_table["statistic"] = corr_table["statistic"].round(4)
                corr_table["p_value"] = corr_table["p_value"].round(4)
            content = html.Div(
                [
                    html.Div(Graph(figure=income_chart), className="panel"),
                    html.Div(
                        [
                            html.Div(correlation_summary(corr_table), className="note"),
                            data_table(
                                "correlation-table",
                                data=table_records(corr_table, max_rows=settings.dashboard.table_max_rows),
                                columns=table_columns(corr_table),
                                page_size=settings.dashboard.table_page_size,
                            ),
                        ],
                        className="panel",
                    ),
                ]
            )
        else:
            sa4_summary = build_sa4_summary_table(scores, poi)
            scores_for_table = score_table(scores)
            poi_summary = poi_summary_table(poi)
            content = html.Div(
                [
                    html.Div(
                        [
                            html.H3("SA4 summary"),
                            data_table(
                                "sa4-summary-table",
                                data=table_records(sa4_summary, max_rows=settings.dashboard.table_max_rows),
                                columns=table_columns(sa4_summary),
                                page_size=settings.dashboard.table_page_size,
                            ),
                        ],
                        className="panel",
                    ),
                    html.Div(
                        [
                            html.H3("SA2 scores"),
                            data_table(
                                "score-table",
                                data=table_records(scores_for_table, max_rows=settings.dashboard.table_max_rows),
                                columns=table_columns(scores_for_table),
                                page_size=settings.dashboard.table_page_size,
                            ),
                        ],
                        className="panel",
                    ),
                    html.Div(
                        [
                            html.H3("POI summary"),
                            data_table(
                                "poi-summary-table",
                                data=table_records(poi_summary, max_rows=settings.dashboard.table_max_rows),
                                columns=table_columns(poi_summary),
                                page_size=settings.dashboard.table_page_size,
                            ),
                        ],
                        className="panel",
                    ),
                ]
            )

        return content, kpis
