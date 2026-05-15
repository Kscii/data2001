"""Gunicorn 使用的 Dash WSGI 入口, 供容器化部署读取同一套配置."""
from __future__ import annotations

import os

from data2001.config import load_settings
from data2001.db.engine import create_engine_from_settings
from data2001.task4.dashboard import create_dashboard_app


config_path = os.getenv("DATA2001_CONFIG", "configs/local.yaml")
settings = load_settings(config_path)
engine = create_engine_from_settings(settings.database)
app = create_dashboard_app(engine, settings)
server = app.server
