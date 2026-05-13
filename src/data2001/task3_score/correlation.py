"""Score 与 median income 的相关性检验逻辑."""
from __future__ import annotations

from typing import Any, cast

from scipy import stats
from sqlalchemy import Engine

from data2001.config import Settings
from data2001.db.repositories.read import select_score_income_sample
from data2001.db.repositories.write import (
    insert_correlation_results,
)
from data2001.task3_score.records import (
    CorrelationResult,
    ScoreIncomeSampleRecord,
    correlation_results_to_db_rows,
)


def _to_float(value: int | float | None) -> float | None:
    """把数据库数值统一成 float；空值继续保留为空."""
    if value is None:
        return None
    return float(value)


def prepare_score_income_sample(
    records: list[ScoreIncomeSampleRecord],
    *,
    min_population: int,
    min_income_earners: int,
) -> list[ScoreIncomeSampleRecord]:
    """保留有 score、median income 且样本量足够的 SA2."""
    sample: list[ScoreIncomeSampleRecord] = []
    for record in records:
        score = _to_float(record.score)
        median_income = _to_float(record.median_income_2022_23)
        population = _to_float(record.population)
        earners = _to_float(record.income_earners_2022_23)
        if score is None or median_income is None or population is None or earners is None:
            continue
        if population < min_population or earners < min_income_earners:
            continue
        sample.append(record)
    return sample


def test_score_income_correlation(
    sample: list[ScoreIncomeSampleRecord],
    *,
    method: str,
    alpha: float,
) -> CorrelationResult:
    """对 score 和 median income 执行 Pearson 或 Spearman 检验."""
    if len(sample) < 3:
        raise ValueError("correlation test 至少需要 3 个 SA2")

    x = [_to_float(record.score) for record in sample]
    y = [_to_float(record.median_income_2022_23) for record in sample]
    clean_x = [value for value in x if value is not None]
    clean_y = [value for value in y if value is not None]

    if method == "pearson":
        result = cast(Any, stats.pearsonr(clean_x, clean_y))
    elif method == "spearman":
        result = cast(Any, stats.spearmanr(clean_x, clean_y))
    else:
        raise ValueError(f"不支持的 correlation method: {method}")

    return CorrelationResult(
        method=method,
        statistic=float(result[0]),
        p_value=float(result[1]),
        n=len(sample),
        alpha=alpha,
    )


def compute_income_correlation(engine: Engine, settings: Settings) -> list[CorrelationResult]:
    """重新计算 score 和 median income 的 Pearson/Spearman correlation."""
    rows = select_score_income_sample(
        engine,
        settings.database.schema_name,
        score_version=settings.task3_score.score_version,
        score_universe=settings.task3_score.score_universe,
    )
    sample_inputs = [ScoreIncomeSampleRecord.from_row(row) for row in rows]
    sample = prepare_score_income_sample(
        sample_inputs,
        min_population=settings.task3_score.min_population,
        min_income_earners=settings.income.min_income_earners,
    )
    results = [
        test_score_income_correlation(
            sample,
            method=settings.correlation.method,
            alpha=settings.correlation.alpha,
        ),
        test_score_income_correlation(
            sample,
            method=settings.correlation.robustness_method,
            alpha=settings.correlation.alpha,
        ),
    ]
    insert_correlation_results(
        engine,
        settings.database.schema_name,
        correlation_results_to_db_rows(
            results,
            score_version=settings.task3_score.score_version,
            score_universe=settings.task3_score.score_universe,
        ),
    )
    return results
