"""统一注册和执行项目 pipeline steps, 供 CLI 和复现流程调用."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import Engine

from data2001_assignment.common.pipeline_plan import resolve_enabled_pipeline_steps
from data2001_assignment.common.progress import PipelineStep, ProgressReporter, run_steps
from data2001_assignment.config import Settings
from data2001_assignment.db.engine import check_connection
from data2001_assignment.db.repositories import (
    check_database,
    clear_database,
    init_database,
    reset_database,
)
from data2001_assignment.task2.planning import build_crawl_plan
from data2001_assignment.task2.pipeline import fetch_poi_raw_and_clean, load_income, run_boundary_pipeline
from data2001_assignment.task3.pipeline import run_compute_score_and_correlation
from data2001_assignment.visualisation.export import generate_report_figures


@dataclass(frozen=True)
class StepDefinition:
    """pipeline registry 中单个步骤的定义."""
    id: str
    name: str
    action: Any


def build_step_registry(
    engine: Engine,
    settings: Settings,
    *,
    reporter: ProgressReporter | None = None,
) -> dict[str, StepDefinition]:
    """构建 step registry, 把 step id 映射到实际执行函数."""
    def init_db_step() -> dict[str, int | str]:
        """初始化数据库 schema、extension、table 和 index."""
        init_database(engine, settings.database)
        return {"init_db": "done"}

    def check_db_step() -> dict[str, int | str]:
        """检查数据库连接、必需表和 PostGIS SRID."""
        check_connection(engine)
        result = check_database(engine, settings.database, settings.spatial.database_srid)
        return {
            "postgis_version": str(result["postgis_version"]),
            "table_count": int(result["table_count"]),
            "missing_tables": str(result["missing_tables"]),
            "bad_srids": str(result["bad_srids"]),
        }

    def plan_crawl_step() -> dict[str, int | str]:
        """根据配置生成抓取计划摘要, 但不请求 POI API."""
        plan = build_crawl_plan(settings)
        return {
            "crawl_scope": plan.scope,
            "sa4_count": plan.sa4_count,
            "sa2_count": plan.sa2_count,
            "sa2_bbox_requests": plan.request_count,
        }

    def boundaries_step() -> dict[str, int | str]:
        """抓取并入库 SA4/SA2 boundary 和 population 数据."""
        return run_boundary_pipeline(engine, settings)

    def fetch_poi_step() -> dict[str, int | str]:
        """抓取 POI raw JSON, 清洗入库并执行 SA2 空间归属."""
        return fetch_poi_raw_and_clean(engine, settings, reporter=reporter)

    def income_step() -> dict[str, int | str]:
        """抓取并入库 SA2 median income 数据."""
        return {"income": load_income(engine, settings)}

    def score_step() -> dict[str, int | str]:
        """重新计算 score 和 income correlation."""
        return run_compute_score_and_correlation(engine, settings)

    def generate_figures_step() -> dict[str, int | str]:
        """生成 report 所需的 Plotly PNG 图."""
        output_paths = generate_report_figures(engine, settings)
        return {name: str(path) for name, path in output_paths.items()}

    def clear_db_step() -> dict[str, int | str]:
        """清空业务表数据, 但保留 schema/table/index."""
        clear_database(engine, settings.database)
        return {"clear_db": "done"}

    def reset_db_step() -> dict[str, int | str]:
        """删除并重建整个业务 schema."""
        reset_database(engine, settings.database)
        return {"reset_db": "done"}

    return {
        "init_db": StepDefinition("init_db", "Initialize database schema", init_db_step),
        "check_db": StepDefinition("check_db", "Check database connection and schema", check_db_step),
        "plan_crawl": StepDefinition("plan_crawl", "Plan crawl scope and requests", plan_crawl_step),
        "load_boundaries": StepDefinition("load_boundaries", "Fetch and load boundaries", boundaries_step),
        "fetch_poi": StepDefinition("fetch_poi", "Fetch raw JSON and clean POI", fetch_poi_step),
        "load_income": StepDefinition("load_income", "Load SA2 income", income_step),
        "compute_score": StepDefinition("compute_score", "Compute score and income correlation", score_step),
        "generate_figures": StepDefinition(
            "generate_figures",
            "Build Plotly figures and export PNG",
            generate_figures_step,
        ),
        "clear_db": StepDefinition("clear_db", "Clear business tables", clear_db_step),
        "reset_db": StepDefinition("reset_db", "Reset schema and reinitialize", reset_db_step),
    }


def execute_pipeline_steps(
    engine: Engine,
    settings: Settings,
    step_ids: list[str],
    *,
    reporter: ProgressReporter | None = None,
    title: str = "Pipeline",
) -> dict[str, int | str]:
    """按给定 step id 顺序执行 pipeline, 并汇总每步返回值."""
    summary: dict[str, int | str] = {}
    registry = build_step_registry(engine, settings, reporter=reporter)
    unknown = sorted({step_id for step_id in step_ids if step_id not in registry})
    if unknown:
        raise ValueError(f"未知 pipeline 步骤: {unknown}; 可选步骤: {sorted(registry)}")

    steps: list[PipelineStep] = []
    for step_id in step_ids:
        definition = registry[step_id]

        def run_step(step_action=definition.action) -> None:
            """执行单个 step 并把结果合并到 summary."""
            summary.update(step_action())

        steps.append(PipelineStep(definition.name, run_step))

    run_steps(title, steps, reporter=reporter)
    return summary


def run_main_pipeline(
    engine: Engine,
    settings: Settings,
    *,
    reporter: ProgressReporter | None = None,
) -> dict[str, int | str]:
    """读取配置中的 enabled steps 并运行主 pipeline."""
    step_ids = resolve_enabled_pipeline_steps(settings)
    return execute_pipeline_steps(engine, settings, step_ids, reporter=reporter, title="Pipeline")
