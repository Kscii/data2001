"""SA2 median income 数据抓取参数和字段标准化函数."""
from __future__ import annotations

from typing import Any

from data2001_assignment.config import IncomeSettings, Settings
from data2001_assignment.task2_import.api.arcgis_client import ArcGISClient
from data2001_assignment.task2_import.records import ArcGISFeature, Sa2IncomeRecord


def build_income_query_params(settings: Settings) -> dict[str, Any]:
    """收入数据按 SA2 code 下载, 入库后和 score 表 join."""
    layer = settings.api.layer("income")
    return {
        "where": "1=1",
        "outFields": ",".join(layer.out_fields),
        "returnGeometry": "false",
        "orderByFields": "sa2_code_2021",
    }


def fetch_sa2_income(client: ArcGISClient, settings: Settings) -> list[ArcGISFeature]:
    """从收入 layer 分页抓取所有 SA2 income features."""
    params = build_income_query_params(settings)
    return list(client.query_features(settings.api.layer("income").url, params, page_size=settings.api.page_size))


def normalize_income_feature(feature: ArcGISFeature, settings: IncomeSettings) -> Sa2IncomeRecord:
    """把 ArcGIS income feature 转成 sa2_income 表字段."""
    attrs = feature["attributes"]
    return Sa2IncomeRecord(
        sa2_code=attrs.get(settings.sa2_code_field),
        sa2_name=attrs.get(settings.sa2_name_field),
        income_earners_2022_23=attrs.get(settings.income_earners_current_field),
        income_earners_2021_22=attrs.get(settings.income_earners_previous_field),
        income_earners_change=attrs.get(settings.income_earners_change_field),
        income_earners_change_pct=attrs.get(settings.income_earners_change_pct_field),
        median_income_2022_23=attrs.get(settings.median_income_field),
        source_year=settings.source_year,
        source_name=settings.source_name,
    )
