"""Task 3 pipeline, 负责计算 SA2 score 并执行收入相关性检验."""
from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine

from data2001_assignment.analysis.correlation import compute_income_correlation
from data2001_assignment.config import Settings
from data2001_assignment.db.repositories import load_score_input, upsert_scores
from data2001_assignment.task2.boundaries import selected_sa4_names
from data2001_assignment.task3.scoring import compute_scores


def run_compute_scores(engine: Engine, settings: Settings) -> pd.DataFrame:
    """读取 score 输入数据, 计算 SA2 score, 并写回 sa2_score 表."""
    rows = load_score_input(
        engine,
        settings.database.schema_name,
        settings.scoring.score_universe,
        selected_sa4_names(settings),
    )
    scores = compute_scores(
        pd.DataFrame(rows),
        score_version=settings.scoring.score_version,
        score_universe=settings.scoring.score_universe,
        min_population=settings.scoring.min_population,
        output_scale=settings.scoring.output_scale,
    )
    upsert_scores(engine, settings.database.schema_name, scores.to_dict("records"))
    return scores


def run_compute_score_and_correlation(engine: Engine, settings: Settings) -> dict[str, int]:
    """依次重新计算 score 和 score-income correlation."""
    scores = run_compute_scores(engine, settings)
    correlations = compute_income_correlation(engine, settings)
    return {
        "scores": len(scores),
        "correlations": len(correlations),
    }
