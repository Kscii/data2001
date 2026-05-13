"""Task 3 的 score 与 correlation 业务记录类型."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ScoreInputRecord:
    """从数据库读取后用于计算 score 的单个 SA2 输入."""
    sa2_code: str
    sa2_name: str | None
    sa4_code: str | None
    sa4_name: str | None
    population: int | float | None
    poi_count: int

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> ScoreInputRecord:
        """把 repository 返回的 row dict 转成显式输入记录."""
        return cls(
            sa2_code=str(row["sa2_code"]),
            sa2_name=row.get("sa2_name"),
            sa4_code=row.get("sa4_code"),
            sa4_name=row.get("sa4_name"),
            population=row.get("population"),
            poi_count=int(row["poi_count"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """转换成 DataFrame 构造时使用的普通字典."""
        return asdict(self)


@dataclass(frozen=True)
class Sa2ScoreRecord:
    """准备写入 sa2_score 表的一条 score 结果."""
    score_version: str
    score_universe: str
    sa2_code: str
    poi_count: int
    mean_poi_count: float
    std_poi_count: float
    z_poi: float
    score_raw: float
    score_100: float
    population: int | float | None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Sa2ScoreRecord:
        """把计算后的 row dict 转成显式 score 记录."""
        return cls(
            score_version=str(row["score_version"]),
            score_universe=str(row["score_universe"]),
            sa2_code=str(row["sa2_code"]),
            poi_count=int(row["poi_count"]),
            mean_poi_count=float(row["mean_poi_count"]),
            std_poi_count=float(row["std_poi_count"]),
            z_poi=float(row["z_poi"]),
            score_raw=float(row["score_raw"]),
            score_100=float(row["score_100"]),
            population=row.get("population"),
        )

    def to_db_dict(self) -> dict[str, Any]:
        """转换成 repository executemany 使用的参数字典."""
        return asdict(self)


@dataclass(frozen=True)
class ScoreIncomeSampleRecord:
    """用于 score-income correlation 检验的一条样本记录."""
    sa2_code: str
    score: float | None
    population: int | float | None
    median_income_2022_23: int | float | None
    income_earners_2022_23: int | float | None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> ScoreIncomeSampleRecord:
        """把 repository 返回的 row dict 转成 correlation 样本记录."""
        score = row.get("score")
        return cls(
            sa2_code=str(row["sa2_code"]),
            score=float(score) if score is not None else None,
            population=row.get("population"),
            median_income_2022_23=row.get("median_income_2022_23"),
            income_earners_2022_23=row.get("income_earners_2022_23"),
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


def score_input_records_to_dataframe(records: list[ScoreInputRecord]) -> pd.DataFrame:
    """把 score 输入记录转换成 Pandas 计算用 DataFrame."""
    return pd.DataFrame([record.to_dict() for record in records])


def score_records_from_dataframe(scores: pd.DataFrame) -> list[Sa2ScoreRecord]:
    """把 score 计算结果 DataFrame 转回显式 score 记录."""
    rows = scores.to_dict("records")
    return [Sa2ScoreRecord.from_row(row) for row in rows]


def score_records_to_db_rows(records: list[Sa2ScoreRecord]) -> list[dict[str, Any]]:
    """把 score dataclass 列表转换成数据库参数列表."""
    return [record.to_db_dict() for record in records]


def correlation_results_to_db_rows(
    results: list[CorrelationResult],
    *,
    score_version: str,
    score_universe: str,
) -> list[dict[str, Any]]:
    """把 correlation 结果转换成 score_income_correlation 表参数."""
    return [
        {
            "score_version": score_version,
            "score_universe": score_universe,
            "method": result.method,
            "statistic": result.statistic,
            "p_value": result.p_value,
            "n": result.n,
            "alpha": result.alpha,
            "is_significant": result.is_significant,
        }
        for result in results
    ]
