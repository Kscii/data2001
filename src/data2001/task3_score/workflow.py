from __future__ import annotations

from sqlalchemy import Engine

from data2001.task3_score.correlation import compute_income_correlation
from data2001.common.types import StepSummary
from data2001.config import Settings
from data2001.db.repositories.read import select_score_input
from data2001.db.repositories.write import upsert_scores
from data2001.task2_import.boundaries.areas import selected_sa4_names
from data2001.task3_score.records import (
    Sa2ScoreRecord,
    ScoreInputRecord,
    score_records_to_db_rows,
)
from data2001.task3_score.scoring import compute_scores


def run_score_calculation(engine: Engine, settings: Settings) -> list[Sa2ScoreRecord]:
    rows = select_score_input(
        engine,
        settings.database.schema_name,
        settings.task3_score.score_universe,
        selected_sa4_names(settings),
    )
    score_inputs = [ScoreInputRecord.from_row(row) for row in rows]
    scores = compute_scores(
        score_inputs,
        score_version=settings.task3_score.score_version,
        score_universe=settings.task3_score.score_universe,
        min_population=settings.task3_score.min_population,
        output_scale=settings.task3_score.output_scale,
    )
    upsert_scores(engine, settings.database.schema_name, score_records_to_db_rows(scores))
    return scores


def run_task3_score_workflow(engine: Engine, settings: Settings) -> StepSummary:
    scores = run_score_calculation(engine, settings)
    correlations = compute_income_correlation(engine, settings)
    return {
        "scores": len(scores),
        "correlations": len(correlations),
    }
