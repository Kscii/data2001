"""数据库连接工具, 负责根据配置创建 SQLAlchemy Engine."""
from __future__ import annotations

from sqlalchemy import Engine, create_engine, text

from data2001_assignment.config import DatabaseSettings


def build_database_url(settings: DatabaseSettings) -> str:
    """根据数据库配置拼出 SQLAlchemy 连接 URL."""
    return (
        f"{settings.driver}://{settings.user}:{settings.password}"
        f"@{settings.host}:{settings.port}/{settings.database}"
    )


def create_engine_from_settings(settings: DatabaseSettings) -> Engine:
    """根据配置创建 SQLAlchemy Engine."""
    return create_engine(build_database_url(settings), future=True)


def check_connection(engine: Engine) -> bool:
    """执行一个最小查询, 用于 CLI/init-db 前确认数据库可用."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
