"""Score 与 median income 的相关性检验逻辑."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from scipy import stats
from sqlalchemy import Engine

from data2001_assignment.config import Settings
from data2001_assignment.db.repositories import (
    insert_correlation_results,
    load_score_income_sample,
)


@dataclass(frozen=True)
class CorrelationResult:
    """score-income correlation 的单个检验结果."""
    method: str
    statistic: float
    p_value: float
    n: int
    alpha: float

    @property
    def is_significant(self) -> bool:
        """判断当前检验结果是否达到配置的显著性水平."""
        return self.p_value < self.alpha


def prepare_score_income_sample(
    df: pd.DataFrame,
    *,
    min_population: int,
    min_income_earners: int,
) -> pd.DataFrame:
    """保留有 score、median income 且样本量足够的 SA2."""
    required = {
        "sa2_code",
        "score",
        "population",
        "median_income_2022_23",
        "income_earners_2022_23",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"correlation 输入缺少字段: {sorted(missing)}")

    sample = df.dropna(subset=["score", "median_income_2022_23"]).copy()
    sample = sample[sample["population"] >= min_population]
    sample = sample[sample["income_earners_2022_23"] >= min_income_earners]
    return sample


def test_score_income_correlation(
    sample: pd.DataFrame,
    *,
    method: str,
    alpha: float,
) -> CorrelationResult:
    """对 score 和 median income 执行 Pearson 或 Spearman 检验."""
    if len(sample) < 3:
        raise ValueError("correlation test 至少需要 3 个 SA2")

    x = sample["score"]
    y = sample["median_income_2022_23"]

    if method == "pearson":
        statistic, p_value = stats.pearsonr(x, y)
    elif method == "spearman":
        statistic, p_value = stats.spearmanr(x, y)
    else:
        raise ValueError(f"不支持的 correlation method: {method}")

    return CorrelationResult(
        method=method,
        statistic=float(statistic),
        p_value=float(p_value),
        n=len(sample),
        alpha=alpha,
    )


def compute_income_correlation(engine: Engine, settings: Settings) -> list[CorrelationResult]:
    """重新计算 score 和 median income 的 Pearson/Spearman correlation."""
    rows = load_score_income_sample(
        engine,
        settings.database.schema_name,
        score_version=settings.scoring.score_version,
        score_universe=settings.scoring.score_universe,
    )
    sample = prepare_score_income_sample(
        pd.DataFrame(rows),
        min_population=settings.scoring.min_population,
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
        [
            {
                "score_version": settings.scoring.score_version,
                "score_universe": settings.scoring.score_universe,
                "method": result.method,
                "statistic": result.statistic,
                "p_value": result.p_value,
                "n": result.n,
                "alpha": result.alpha,
                "is_significant": result.is_significant,
            }
            for result in results
        ],
    )
    return results
