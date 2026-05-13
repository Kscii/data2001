"""Dashboard 页面布局, 只负责控件和页面结构."""
from __future__ import annotations

from dash import html
from dash.dcc.Dropdown import Dropdown
from dash.dcc.Input import Input as DccInput
from dash.dcc.Tab import Tab
from dash.dcc.Tabs import Tabs
from sqlalchemy import Engine

from data2001.config import Settings
from data2001.task4_visuals.dashboard.helpers import initial_options

DASH_INDEX_STRING = """
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


def create_dashboard_layout(engine: Engine, settings: Settings) -> html.Div:
    """生成 Dash 页面布局, 并用数据库现有值初始化筛选器."""
    options = initial_options(engine, settings)
    return html.Div(
        [
            html.Div(
                [
                    html.Aside(
                        [
                            html.H1(settings.dashboard.title, className="title"),
                            html.Div("Read-only dashboard backed by PostgreSQL/PostGIS.", className="subtitle"),
                            html.Div("SA4", className="control-label"),
                            Dropdown(
                                id="sa4-filter",
                                options=options["sa4"],
                                multi=True,
                                placeholder="All SA4 regions",
                            ),
                            html.Div("SA2", className="control-label"),
                            Dropdown(
                                id="sa2-filter",
                                options=options["sa2"],
                                multi=True,
                                placeholder="All SA2 regions",
                            ),
                            html.Div("POI group", className="control-label"),
                            Dropdown(
                                id="poi-group-filter",
                                options=options["poi_groups"],
                                multi=True,
                                placeholder="All POI groups",
                            ),
                            html.Div("Ranked SA2 count", className="control-label"),
                            DccInput(
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
                            Tabs(
                                id="main-tabs",
                                value="overview",
                                className="tabs",
                                children=[
                                    Tab(label="Overview", value="overview"),
                                    Tab(label="Score Map", value="score-map"),
                                    Tab(label="POI Map", value="poi-map"),
                                    Tab(label="Income", value="income"),
                                    Tab(label="Tables", value="tables"),
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
