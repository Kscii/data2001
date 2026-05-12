"""只读 Dash dashboard, 复用查询层和 Plotly builder 展示数据库现有结果."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dash_table, dcc, html
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from data2001_assignment.config import Settings
from data2001_assignment.visualisation.figures import (
    build_bottom_sa2_bar,
    build_poi_group_distribution,
    build_poi_group_by_sa4_bar,
    build_sa4_score_boxplot,
    build_score_histogram,
    build_score_income_scatter,
    build_top_sa2_bar,
)
from data2001_assignment.visualisation.maps import (
    build_poi_point_scatter_map,
    build_score_choropleth_map,
)
from data2001_assignment.visualisation.queries import (
    load_correlation_results,
    load_poi_points,
    load_sa2_scores,
    load_score_income,
)
from data2001_assignment.visualisation.tables import build_sa4_summary_table


def _empty_figure(title: str, message: str = "No data available") -> go.Figure:
    """构建空状态图表, 避免数据库暂无数据时 Dash 页面报错."""
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


def _as_list(value: Any) -> list[Any]:
    """把 Dash 单选、多选或空值统一转换成列表."""
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def _options(values: list[Any]) -> list[dict[str, Any]]:
    """把普通值列表转换成 Dash Dropdown 使用的 options."""
    return [{"label": str(value), "value": value} for value in values if value is not None]


def _safe_load(default: Any, loader):
    """安全执行初始化查询, 数据库未准备好时返回默认值."""
    try:
        return loader()
    except SQLAlchemyError:
        return default


def _filter_common(df: pd.DataFrame, *, sa4_names: list[str], sa2_codes: list[str]) -> pd.DataFrame:
    """按 SA4 和 SA2 筛选带空间区域字段的 DataFrame."""
    if df.empty:
        return df
    result = df
    if sa4_names and "sa4_name" in result.columns:
        result = result[result["sa4_name"].isin(sa4_names)]
    if sa2_codes and "sa2_code" in result.columns:
        result = result[result["sa2_code"].isin(sa2_codes)]
    return result


def _filter_poi(
    poi_df: pd.DataFrame,
    *,
    sa4_names: list[str],
    sa2_codes: list[str],
    poi_groups: list[str],
) -> pd.DataFrame:
    """按 SA4、SA2 和 POI group 筛选 POI 点数据."""
    result = _filter_common(poi_df, sa4_names=sa4_names, sa2_codes=sa2_codes)
    if not result.empty and poi_groups and "poigroup_name" in result.columns:
        result = result[result["poigroup_name"].isin(poi_groups)]
    return result


def _poi_group_counts(poi_df: pd.DataFrame) -> pd.DataFrame:
    """把当前筛选后的 POI 点聚合成 POI group 数量表."""
    if poi_df.empty:
        return pd.DataFrame(columns=["poigroup_name", "poigroup_code", "poi_count"])
    return (
        poi_df.groupby(["poigroup_name", "poigroup_code"], dropna=False)
        .size()
        .reset_index(name="poi_count")
        .sort_values(["poi_count", "poigroup_name"], ascending=[False, True])
    )


def _table_columns(df: pd.DataFrame) -> list[dict[str, str]]:
    """把 DataFrame 列名转换成 Dash DataTable 的列配置."""
    return [{"name": column, "id": column} for column in df.columns]


def _records(df: pd.DataFrame, *, max_rows: int) -> list[dict[str, Any]]:
    """把 DataFrame 转成 DataTable records, 并限制默认展示行数."""
    if df.empty:
        return []
    return df.head(max_rows).to_dict("records")


def _score_table(scores: pd.DataFrame) -> pd.DataFrame:
    """整理 SA2 score 表格, 只保留 dashboard 需要展示的字段."""
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
    result = scores[columns].copy()
    result["score_100"] = result["score_100"].round(2)
    result["z_poi"] = result["z_poi"].round(3)
    return result.sort_values("score_100", ascending=False)


def _poi_summary_table(poi_df: pd.DataFrame) -> pd.DataFrame:
    """按 SA4、SA2 和 POI group 汇总当前 POI 数量."""
    columns = ["sa4_name", "sa2_name", "poigroup_name", "poi_count"]
    if poi_df.empty:
        return pd.DataFrame(columns=columns)
    return (
        poi_df.groupby(["sa4_name", "sa2_name", "poigroup_name"], dropna=False)
        .size()
        .reset_index(name="poi_count")
        .sort_values("poi_count", ascending=False)
    )


def _correlation_summary(correlation: pd.DataFrame) -> str:
    """根据最新 correlation 结果生成简短解释文本."""
    if correlation.empty:
        return "No correlation test result is available for the current score configuration."
    significant = correlation[correlation["is_significant"].astype(bool)]
    if significant.empty:
        return "No statistically significant relationship found between score and median income."
    methods = ", ".join(significant["method"].astype(str).str.title().tolist())
    return f"Statistically significant relationship found for: {methods}."


def _kpi_cards(scores: pd.DataFrame, poi_df: pd.DataFrame, score_income: pd.DataFrame) -> list[html.Div]:
    """根据当前筛选结果生成顶部 KPI 卡片."""
    values = [
        ("SA2 regions", len(scores)),
        ("Assigned POI", len(poi_df)),
        ("Mean score", f"{scores['score_100'].mean():.1f}" if not scores.empty else "n/a"),
        ("Income sample", len(score_income)),
    ]
    return [
        html.Div(
            [html.Div(label, className="kpi-label"), html.Div(str(value), className="kpi-value")],
            className="kpi-card",
        )
        for label, value in values
    ]


def _data_table(
    table_id: str,
    *,
    data: list[dict[str, Any]] | None = None,
    columns: list[dict[str, str]] | None = None,
    page_size: int,
) -> dash_table.DataTable:
    """创建统一样式的 Dash DataTable."""
    return dash_table.DataTable(
        id=table_id,
        data=data or [],
        columns=columns or [],
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


def _initial_options(engine: Engine, settings: Settings) -> dict[str, list[dict[str, Any]]]:
    """页面首次加载时从数据库读取筛选器候选值."""
    schema = settings.database.schema_name
    scores = _safe_load(pd.DataFrame(), lambda: load_sa2_scores(
        engine,
        schema,
        score_version=settings.scoring.score_version,
        score_universe=settings.scoring.score_universe,
    ))
    poi = _safe_load(pd.DataFrame(), lambda: load_poi_points(engine, schema, limit=settings.dashboard.poi_limit))
    return {
        "sa4": _options(sorted(scores.get("sa4_name", pd.Series(dtype=str)).dropna().unique().tolist())),
        "sa2": _options(sorted(scores.get("sa2_code", pd.Series(dtype=str)).dropna().unique().tolist())),
        "poi_groups": _options(sorted(poi.get("poigroup_name", pd.Series(dtype=str)).dropna().unique().tolist())),
    }


def create_dashboard_app(engine: Engine, settings: Settings) -> Dash:
    """创建只读 Dash app, 并把查询函数和 Plotly 图表接到 callback."""
    app = Dash(__name__, title=settings.dashboard.title)
    app.index_string = """
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                body { margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #111827; }
                .shell { display: grid; grid-template-columns: 280px minmax(0, 1fr); min-height: 100vh; background: #f8fafc; }
                .sidebar { padding: 18px; border-right: 1px solid #e5e7eb; background: #ffffff; }
                .main { padding: 18px 22px 28px; }
                .title { font-size: 22px; font-weight: 750; margin: 0 0 4px; }
                .subtitle { color: #6b7280; font-size: 13px; margin-bottom: 18px; }
                .control-label { font-size: 12px; font-weight: 700; margin: 14px 0 6px; color: #374151; }
                .tabs .tab { padding: 10px 14px; }
                .panel { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; margin-top: 12px; }
                .grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
                .kpi-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 12px; }
                .kpi-card { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; }
                .kpi-label { font-size: 12px; color: #6b7280; margin-bottom: 4px; }
                .kpi-value { font-size: 22px; font-weight: 760; }
                .map-graph { height: 72vh; min-height: 620px; }
                .note { color: #374151; font-size: 14px; line-height: 1.45; margin: 2px 0 12px; }
                @media (max-width: 900px) {
                    .shell { grid-template-columns: 1fr; }
                    .sidebar { border-right: 0; border-bottom: 1px solid #e5e7eb; }
                    .grid-2, .kpi-row { grid-template-columns: 1fr; }
                    .map-graph { height: 68vh; min-height: 460px; }
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    """
    schema = settings.database.schema_name

    def serve_layout() -> html.Div:
        """生成 Dash 页面布局, 并用数据库现有值初始化筛选器."""
        initial = _initial_options(engine, settings)
        return html.Div(
            [
                html.Div(
                [
                    html.Aside(
                        [
                            html.H1(settings.dashboard.title, className="title"),
                            html.Div("Read-only dashboard backed by PostgreSQL/PostGIS.", className="subtitle"),
                            html.Div("SA4", className="control-label"),
                            dcc.Dropdown(
                                id="sa4-filter",
                                options=initial["sa4"],
                                multi=True,
                                placeholder="All SA4 regions",
                            ),
                            html.Div("SA2", className="control-label"),
                            dcc.Dropdown(
                                id="sa2-filter",
                                options=initial["sa2"],
                                multi=True,
                                placeholder="All SA2 regions",
                            ),
                            html.Div("POI group", className="control-label"),
                            dcc.Dropdown(
                                id="poi-group-filter",
                                options=initial["poi_groups"],
                                multi=True,
                                placeholder="All POI groups",
                            ),
                            html.Div("Ranked SA2 count", className="control-label"),
                            dcc.Input(
                                id="top-n",
                                type="number",
                                min=3,
                                max=100,
                                step=1,
                                value=settings.dashboard.default_top_n,
                                style={"width": "100%"},
                            ),
                        ],
                        className="sidebar",
                    ),
                    html.Main(
                        [
                            html.Div(id="kpi-row", className="kpi-row"),
                            dcc.Tabs(
                                id="main-tabs",
                                value="overview",
                                className="tabs",
                                children=[
                                    dcc.Tab(label="Overview", value="overview"),
                                    dcc.Tab(label="Score Map", value="score-map"),
                                    dcc.Tab(label="POI Map", value="poi-map"),
                                    dcc.Tab(label="Income", value="income"),
                                    dcc.Tab(label="Tables", value="tables"),
                                ],
                            ),
                            html.Div(id="tab-content"),
                        ],
                        className="main",
                    ),
                ],
                className="shell",
                ),
            ]
        )

    app.layout = serve_layout

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
        sa4_names = _as_list(sa4_value)
        sa2_codes = _as_list(sa2_value)
        poi_groups = _as_list(group_value)
        n = max(int(top_n or settings.dashboard.default_top_n), 1)
        try:
            scores = load_sa2_scores(
                engine,
                schema,
                score_version=settings.scoring.score_version,
                score_universe=settings.scoring.score_universe,
            )
            poi = load_poi_points(engine, schema, limit=settings.dashboard.poi_limit)
            score_income = load_score_income(
                engine,
                schema,
                score_version=settings.scoring.score_version,
                score_universe=settings.scoring.score_universe,
            )
            correlation = load_correlation_results(
                engine,
                schema,
                score_version=settings.scoring.score_version,
                score_universe=settings.scoring.score_universe,
            )
        except SQLAlchemyError as exc:
            message = html.Div(f"Database query failed: {exc}", className="panel")
            return message, _kpi_cards(pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

        scores = _filter_common(scores, sa4_names=sa4_names, sa2_codes=sa2_codes)
        poi = _filter_poi(poi, sa4_names=sa4_names, sa2_codes=sa2_codes, poi_groups=poi_groups)
        score_income = _filter_common(score_income, sa4_names=sa4_names, sa2_codes=sa2_codes)
        kpis = _kpi_cards(scores, poi, score_income)

        score_histogram = (
            build_score_histogram(scores, nbins=settings.figures.score_histogram_nbins)
            if not scores.empty
            else _empty_figure("Distribution of SA2 well-resourced scores")
        )
        top_bar = build_top_sa2_bar(scores, n=n) if not scores.empty else _empty_figure(f"Top {n} SA2s by score")
        bottom_bar = (
            build_bottom_sa2_bar(scores, n=n)
            if not scores.empty
            else _empty_figure(f"Bottom {n} SA2s by score")
        )
        sa4_boxplot = (
            build_sa4_score_boxplot(scores)
            if not scores.empty
            else _empty_figure("SA2 score distribution by SA4")
        )
        score_map = (
            build_score_choropleth_map(scores)
            if not scores.empty
            else _empty_figure("SA2 well-resourced score map")
        )
        poi_map = (
            build_poi_point_scatter_map(poi)
            if not poi.empty
            else _empty_figure("POI point locations")
        )
        group_counts = _poi_group_counts(poi)
        group_chart = (
            build_poi_group_distribution(group_counts)
            if not group_counts.empty
            else _empty_figure("POI group distribution")
        )
        group_by_sa4_chart = (
            build_poi_group_by_sa4_bar(poi)
            if not poi.empty
            else _empty_figure("POI group composition by SA4")
        )
        income_chart = (
            build_score_income_scatter(score_income)
            if not score_income.empty
            else _empty_figure("Well-resourced score vs median income")
        )

        if tab == "overview":
            content = html.Div(
                [
                    html.Div(
                        [
                            html.Div(dcc.Graph(figure=score_histogram), className="panel"),
                            html.Div(dcc.Graph(figure=sa4_boxplot), className="panel"),
                        ],
                        className="grid-2",
                    ),
                    html.Div(
                        [
                            html.Div(dcc.Graph(figure=top_bar), className="panel"),
                            html.Div(dcc.Graph(figure=bottom_bar), className="panel"),
                        ],
                        className="grid-2",
                    ),
                ]
        )
        elif tab == "score-map":
            content = html.Div(dcc.Graph(figure=score_map, className="map-graph"), className="panel")
        elif tab == "poi-map":
            content = html.Div(
                [
                    html.Div(dcc.Graph(figure=poi_map, className="map-graph"), className="panel"),
                    html.Div(
                        [
                            html.Div(dcc.Graph(figure=group_chart), className="panel"),
                            html.Div(dcc.Graph(figure=group_by_sa4_chart), className="panel"),
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
                    html.Div(dcc.Graph(figure=income_chart), className="panel"),
                    html.Div(
                        [
                            html.Div(_correlation_summary(corr_table), className="note"),
                            _data_table(
                                "correlation-table",
                                data=_records(corr_table, max_rows=settings.dashboard.table_max_rows),
                                columns=_table_columns(corr_table),
                                page_size=settings.dashboard.table_page_size,
                            ),
                        ],
                        className="panel",
                    ),
                ]
            )
        else:
            sa4_summary = build_sa4_summary_table(scores, poi)
            score_table = _score_table(scores)
            poi_summary = _poi_summary_table(poi)
            content = html.Div(
                [
                    html.Div(
                        [
                            html.H3("SA4 summary"),
                            _data_table(
                                "sa4-summary-table",
                                data=_records(sa4_summary, max_rows=settings.dashboard.table_max_rows),
                                columns=_table_columns(sa4_summary),
                                page_size=settings.dashboard.table_page_size,
                            ),
                        ],
                        className="panel",
                    ),
                    html.Div(
                        [
                            html.H3("SA2 scores"),
                            _data_table(
                                "score-table",
                                data=_records(score_table, max_rows=settings.dashboard.table_max_rows),
                                columns=_table_columns(score_table),
                                page_size=settings.dashboard.table_page_size,
                            ),
                        ],
                        className="panel",
                    ),
                    html.Div(
                        [
                            html.H3("POI summary"),
                            _data_table(
                                "poi-summary-table",
                                data=_records(poi_summary, max_rows=settings.dashboard.table_max_rows),
                                columns=_table_columns(poi_summary),
                                page_size=settings.dashboard.table_page_size,
                            ),
                        ],
                        className="panel",
                    ),
                ]
            )

        return content, kpis

    return app
