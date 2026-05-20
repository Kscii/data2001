from __future__ import annotations

from sqlalchemy import Engine, create_engine, text

from data2001.config import DatabaseSettings


def build_database_url(settings: DatabaseSettings) -> str:
    return (
        f"{settings.driver}://{settings.user}:{settings.password}"
        f"@{settings.host}:{settings.port}/{settings.database}"
    )


def create_engine_from_settings(settings: DatabaseSettings) -> Engine:
    return create_engine(build_database_url(settings), future=True)


def check_connection(engine: Engine) -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
