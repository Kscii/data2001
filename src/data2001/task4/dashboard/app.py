"""Dash dashboard app 创建入口."""
from __future__ import annotations

from dash import Dash
from sqlalchemy import Engine

from data2001.config import Settings
from data2001.task4.dashboard.callbacks import register_dashboard_callbacks
from data2001.task4.dashboard.layout import DASH_INDEX_STRING, create_dashboard_layout


def create_dashboard_app(engine: Engine, settings: Settings) -> Dash:
    """创建只读 Dash app, 并连接 layout 和 callbacks."""
    app = Dash(__name__, title=settings.dashboard.title)
    app.index_string = DASH_INDEX_STRING
    app.layout = lambda: create_dashboard_layout(engine, settings)
    register_dashboard_callbacks(app, engine, settings)
    return app
