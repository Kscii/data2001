"""Task 2 总流程：按显式顺序运行 boundary、POI 和 income import."""
from __future__ import annotations

from sqlalchemy import Engine

from data2001.common.types import StepSummary
from data2001.config import Settings
from data2001.task2_import.boundaries.boundary_import import run_boundary_import
from data2001.task2_import.income.income_import import run_income_import
from data2001.task2_import.poi.poi_import import run_poi_import


def run_task2_import_workflow(engine: Engine, settings: Settings) -> StepSummary:
    """运行 Task 2 的完整数据准备流程."""
    summary = run_boundary_import(engine, settings)
    summary.update(run_poi_import(engine, settings))
    summary["income"] = run_income_import(engine, settings)
    return summary
