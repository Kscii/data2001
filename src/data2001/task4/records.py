"""Task 4 的只读展示记录类型, 连接查询层和图表层."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class Sa2ScoreView:
    """图表和地图使用的一条 SA2 score 展示记录."""
    sa2_code: str
    sa2_name: str | None
    sa4_code: str | None
    sa4_name: str | None
    population: int | float | None
    poi_count: int
    mean_poi_count: float
    std_poi_count: float
    z_poi: float
    score_raw: float
    score_100: float
    geometry: Any

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Sa2ScoreView:
        """把 SQL row 转成 SA2 score 展示记录."""
        return cls(
            sa2_code=str(row["sa2_code"]),
            sa2_name=row.get("sa2_name"),
            sa4_code=row.get("sa4_code"),
            sa4_name=row.get("sa4_name"),
            population=row.get("population"),
            poi_count=int(row["poi_count"]),
            mean_poi_count=float(row["mean_poi_count"]),
            std_poi_count=float(row["std_poi_count"]),
            z_poi=float(row["z_poi"]),
            score_raw=float(row["score_raw"]),
            score_100=float(row["score_100"]),
            geometry=row.get("geometry"),
        )


@dataclass(frozen=True)
class PoiGroupCountView:
    """POI group 数量图使用的一条聚合记录."""
    poigroup_name: str
    poigroup_code: int | str | None
    poi_count: int

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> PoiGroupCountView:
        """把 SQL row 转成 POI group 数量记录."""
        return cls(
            poigroup_name=str(row["poigroup_name"]),
            poigroup_code=row.get("poigroup_code"),
            poi_count=int(row["poi_count"]),
        )


@dataclass(frozen=True)
class PoiPointView:
    """POI 地图和 dashboard 筛选使用的一条点位记录."""
    objectid: int
    poigroup_code: int | str | None
    poigroup_name: str
    poitype: str | None
    poiname: str | None
    longitude: float
    latitude: float
    sa2_code: str | None
    sa2_name: str | None
    sa4_code: str | None
    sa4_name: str | None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> PoiPointView:
        """把 SQL row 转成 POI 点位展示记录."""
        return cls(
            objectid=int(row["objectid"]),
            poigroup_code=row.get("poigroup_code"),
            poigroup_name=str(row["poigroup_name"]),
            poitype=row.get("poitype"),
            poiname=row.get("poiname"),
            longitude=float(row["longitude"]),
            latitude=float(row["latitude"]),
            sa2_code=row.get("sa2_code"),
            sa2_name=row.get("sa2_name"),
            sa4_code=row.get("sa4_code"),
            sa4_name=row.get("sa4_name"),
        )


@dataclass(frozen=True)
class ScoreIncomeView:
    """score-income 散点图使用的一条 join 后记录."""
    sa2_code: str
    sa2_name: str | None
    sa4_name: str | None
    score_100: float
    poi_count: int
    population: int | float | None
    median_income_2022_23: int | float | None
    income_earners_2022_23: int | float | None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> ScoreIncomeView:
        """把 SQL row 转成 score-income 展示记录."""
        return cls(
            sa2_code=str(row["sa2_code"]),
            sa2_name=row.get("sa2_name"),
            sa4_name=row.get("sa4_name"),
            score_100=float(row["score_100"]),
            poi_count=int(row["poi_count"]),
            population=row.get("population"),
            median_income_2022_23=row.get("median_income_2022_23"),
            income_earners_2022_23=row.get("income_earners_2022_23"),
        )


@dataclass(frozen=True)
class CorrelationResultView:
    """dashboard 展示的最新 correlation 检验结果."""
    method: str
    statistic: float
    p_value: float
    n: int
    alpha: float
    is_significant: bool
    created_at: datetime | str | None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> CorrelationResultView:
        """把 SQL row 转成 correlation 展示记录."""
        return cls(
            method=str(row["method"]),
            statistic=float(row["statistic"]),
            p_value=float(row["p_value"]),
            n=int(row["n"]),
            alpha=float(row["alpha"]),
            is_significant=bool(row["is_significant"]),
            created_at=row.get("created_at"),
        )


def sa2_score_views_to_dataframe(records: list[Sa2ScoreView]) -> pd.DataFrame:
    """把 SA2 score view 列表转换成图表使用的 DataFrame."""
    return pd.DataFrame([asdict(record) for record in records])


def poi_group_count_views_to_dataframe(records: list[PoiGroupCountView]) -> pd.DataFrame:
    """把 POI group count view 列表转换成图表使用的 DataFrame."""
    return pd.DataFrame([asdict(record) for record in records])


def poi_point_views_to_dataframe(records: list[PoiPointView]) -> pd.DataFrame:
    """把 POI point view 列表转换成地图和 dashboard 使用的 DataFrame."""
    return pd.DataFrame([asdict(record) for record in records])


def score_income_views_to_dataframe(records: list[ScoreIncomeView]) -> pd.DataFrame:
    """把 score-income view 列表转换成散点图使用的 DataFrame."""
    return pd.DataFrame([asdict(record) for record in records])


def correlation_result_views_to_dataframe(records: list[CorrelationResultView]) -> pd.DataFrame:
    """把 correlation result view 列表转换成 dashboard 表格使用的 DataFrame."""
    return pd.DataFrame([asdict(record) for record in records])
