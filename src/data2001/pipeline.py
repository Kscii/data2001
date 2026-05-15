"""Explicit workflow step catalog and runner."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import Engine

from data2001.common.progress import ProgressReporter, WorkflowStep, run_steps
from data2001.common.types import StepSummary
from data2001.config import Settings
from data2001.db.engine import check_connection
from data2001.db.repositories.admin import (
    check_database,
    clear_database,
    init_database,
    reset_database,
)
from data2001.task2_import.planning import build_crawl_plan
from data2001.task2_import.workflow import (
    run_boundary_import,
    run_income_import,
    run_poi_import,
)
from data2001.task3_score.workflow import run_task3_score_workflow
from data2001.task4.export import export_report_charts


@dataclass(frozen=True)
class StepContext:
    """Runtime objects shared by workflow steps."""
    engine: Engine
    settings: Settings
    reporter: ProgressReporter | None = None


@dataclass(frozen=True)
class StepDefinition:
    """One explicit workflow step and its CLI command."""
    id: str
    command: str
    name: str
    is_destructive: bool
    run: Callable[[StepContext], StepSummary]


def run_init_db_step(context: StepContext) -> StepSummary:
    """Initialize schema, extensions, tables, and indexes."""
    init_database(context.engine, context.settings.database)
    return {"init_db": "done"}


def run_check_db_step(context: StepContext) -> StepSummary:
    """Check database connection, required tables, PostGIS, and SRID."""
    check_connection(context.engine)
    result = check_database(
        context.engine,
        context.settings.database,
        context.settings.spatial.database_srid,
    )
    return {
        "postgis_version": str(result["postgis_version"]),
        "table_count": int(result["table_count"]),
        "missing_tables": str(result["missing_tables"]),
        "bad_srids": str(result["bad_srids"]),
    }


def run_plan_import_step(context: StepContext) -> StepSummary:
    """Build the import plan without importing POI data."""
    plan = build_crawl_plan(context.settings)
    return {
        "crawl_scope": plan.scope,
        "sa4_count": plan.sa4_count,
        "sa2_count": plan.sa2_count,
        "sa2_bbox_requests": plan.request_count,
    }


def run_import_boundaries_step(context: StepContext) -> StepSummary:
    """Import SA4, SA2, and population data."""
    return run_boundary_import(context.engine, context.settings)


def run_import_poi_step(context: StepContext) -> StepSummary:
    """Import raw POI JSON, clean POI records, and assign them to SA2."""
    return run_poi_import(context.engine, context.settings, reporter=context.reporter)


def run_import_income_step(context: StepContext) -> StepSummary:
    """Import SA2 median income data."""
    return {"income": run_income_import(context.engine, context.settings)}


def run_compute_score_step(context: StepContext) -> StepSummary:
    """Compute SA2 scores and score-income correlation."""
    return run_task3_score_workflow(context.engine, context.settings)


def run_export_charts_step(context: StepContext) -> StepSummary:
    """Export report PNG charts."""
    output_paths = export_report_charts(context.engine, context.settings)
    return {name: str(path) for name, path in output_paths.items()}


def run_clear_db_step(context: StepContext) -> StepSummary:
    """Clear business table data while keeping schema and indexes."""
    clear_database(context.engine, context.settings.database)
    return {"clear_db": "done"}


def run_reset_db_step(context: StepContext) -> StepSummary:
    """Drop and rebuild the whole business schema."""
    reset_database(context.engine, context.settings.database)
    return {"reset_db": "done"}


STEP_DEFINITIONS = [
    StepDefinition("init_db", "init-db", "Initialize database schema", False, run_init_db_step),
    StepDefinition("check_db", "check-db", "Check database connection and schema", False, run_check_db_step),
    StepDefinition("plan_import", "plan-import", "Plan import scope and requests", False, run_plan_import_step),
    StepDefinition("import_boundaries", "import-boundaries", "Import boundaries and population", False, run_import_boundaries_step),
    StepDefinition("import_poi", "import-poi", "Import raw JSON and clean POI", False, run_import_poi_step),
    StepDefinition("import_income", "import-income", "Import SA2 income", False, run_import_income_step),
    StepDefinition("compute_score", "compute-score", "Compute score and income correlation", False, run_compute_score_step),
    StepDefinition("export_charts", "generate-figures", "Build Plotly charts and export PNG", False, run_export_charts_step),
    StepDefinition("clear_db", "clear-db", "Clear business tables", True, run_clear_db_step),
    StepDefinition("reset_db", "reset-db", "Reset schema and reinitialize", True, run_reset_db_step),
]


def step_registry() -> dict[str, StepDefinition]:
    """Return workflow steps by step id."""
    return {definition.id: definition for definition in STEP_DEFINITIONS}


def command_registry() -> dict[str, StepDefinition]:
    """Return workflow steps by CLI command."""
    return {definition.command: definition for definition in STEP_DEFINITIONS}


def resolve_enabled_workflow_steps(settings: Settings) -> list[str]:
    """Validate and return enabled workflow step ids."""
    available = [definition.id for definition in STEP_DEFINITIONS]
    enabled = settings.workflow.enabled_steps

    if not enabled:
        raise ValueError("workflow.enabled_steps must not be empty")

    unknown = sorted({step_id for step_id in enabled if step_id not in available})
    if unknown:
        raise ValueError(f"workflow.enabled_steps has unknown steps: {unknown}; available={available}")

    duplicated = sorted({step_id for step_id in enabled if enabled.count(step_id) > 1})
    if duplicated:
        raise ValueError(f"workflow.enabled_steps has duplicated steps: {duplicated}")

    return enabled


def has_destructive_steps(step_ids: list[str]) -> bool:
    """Return True if any step id points to a destructive database command."""
    registry = step_registry()
    return any(registry[step_id].is_destructive for step_id in step_ids)


def execute_workflow_steps(
    engine: Engine,
    settings: Settings,
    step_ids: list[str],
    *,
    reporter: ProgressReporter | None = None,
    title: str = "Workflow",
) -> StepSummary:
    """Run workflow steps in order and merge their summaries."""
    summary: StepSummary = {}
    registry = step_registry()
    unknown = sorted({step_id for step_id in step_ids if step_id not in registry})
    if unknown:
        raise ValueError(f"Unknown workflow steps: {unknown}; available={sorted(registry)}")

    context = StepContext(engine=engine, settings=settings, reporter=reporter)
    steps: list[WorkflowStep] = []
    for step_id in step_ids:
        definition = registry[step_id]

        def run_step(step_definition: StepDefinition = definition) -> None:
            summary.update(step_definition.run(context))

        steps.append(WorkflowStep(definition.name, run_step))

    run_steps(title, steps, reporter=reporter)
    return summary


def run_main_workflow(
    engine: Engine,
    settings: Settings,
    *,
    reporter: ProgressReporter | None = None,
) -> StepSummary:
    """Run the configured main workflow."""
    step_ids = resolve_enabled_workflow_steps(settings)
    return execute_workflow_steps(engine, settings, step_ids, reporter=reporter, title="Workflow")
