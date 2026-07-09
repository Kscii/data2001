"""Command line entrypoint for database, workflow, and dashboard actions."""
from __future__ import annotations

import argparse
from collections.abc import Callable

from sqlalchemy.exc import SQLAlchemyError

from data2001.common.progress import ProgressReporter
from data2001.common.types import StepSummary
from data2001.config import load_settings
from data2001.db.engine import create_engine_from_settings
from data2001.pipeline import (
    STEP_DEFINITIONS,
    command_registry,
    execute_workflow_steps,
    has_destructive_steps,
    resolve_enabled_workflow_steps,
    run_main_workflow,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser from the explicit step catalog."""
    top_level_parser = argparse.ArgumentParser(add_help=False)
    top_level_parser.add_argument("--config", default="configs/local.yaml")

    command_parser = argparse.ArgumentParser(add_help=False)
    command_parser.add_argument("--config", default=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(prog="sra-explorer", parents=[top_level_parser])
    subparsers = parser.add_subparsers(dest="command", required=True)

    for definition in STEP_DEFINITIONS:
        step_parser = subparsers.add_parser(definition.command, parents=[command_parser])
        if definition.is_destructive:
            step_parser.add_argument("--yes", action="store_true")

    workflow_parser = subparsers.add_parser("run-workflow", parents=[command_parser])
    workflow_parser.add_argument("--yes", action="store_true")

    subparsers.add_parser("dashboard", parents=[command_parser])
    return parser


def _require_yes(command: str, yes: bool) -> None:
    """Require --yes for destructive commands."""
    if not yes:
        raise SystemExit(f"{command} is destructive. Add --yes to run it.")


def _print_summary(summary: StepSummary) -> None:
    """Print a workflow summary as key=value lines."""
    for key, value in summary.items():
        print(f"{key}={value}")


def _run_db_command(action: Callable[[], None]) -> None:
    """Run a database action and present SQLAlchemy errors as CLI errors."""
    try:
        action()
    except SQLAlchemyError as exc:
        raise SystemExit(f"Database operation failed: {exc}") from exc


def main() -> None:
    """Parse CLI arguments and run the selected command."""
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(args.config)
    engine = create_engine_from_settings(settings.database)
    reporter = ProgressReporter(enabled=settings.progress.enabled)
    commands = command_registry()

    if args.command in commands:
        definition = commands[args.command]
        if definition.is_destructive:
            _require_yes(args.command, args.yes)

        def action() -> None:
            _print_summary(
                execute_workflow_steps(
                    engine,
                    settings,
                    [definition.id],
                    reporter=reporter,
                    title=args.command,
                )
            )

        _run_db_command(action)
        return

    if args.command == "run-workflow":
        step_ids = resolve_enabled_workflow_steps(settings)
        if has_destructive_steps(step_ids):
            _require_yes("run-workflow (contains clear-db/reset-db)", args.yes)

        def action() -> None:
            _print_summary(run_main_workflow(engine, settings, reporter=reporter))

        _run_db_command(action)
        return

    if args.command == "dashboard":
        from data2001.task4.dashboard import create_dashboard_app

        app = create_dashboard_app(engine, settings)
        app.run(
            host=settings.dashboard.host,
            port=settings.dashboard.port,
            debug=settings.dashboard.debug,
        )
        return

    raise NotImplementedError(f"{args.command} is not implemented")


if __name__ == "__main__":
    main()
