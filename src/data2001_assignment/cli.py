"""项目命令行入口, 负责把 CLI 命令分发到数据库、pipeline 和 dashboard."""
from __future__ import annotations

import argparse

from sqlalchemy.exc import SQLAlchemyError

from data2001_assignment.common.pipeline_plan import resolve_enabled_pipeline_steps
from data2001_assignment.common.progress import ProgressReporter
from data2001_assignment.config import load_settings
from data2001_assignment.db.engine import create_engine_from_settings
from data2001_assignment.pipeline import execute_pipeline_steps, run_main_pipeline


def build_parser() -> argparse.ArgumentParser:
    """构建 data2001 命令行参数和子命令."""
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--config", default="configs/local.yaml")

    parser = argparse.ArgumentParser(prog="data2001", parents=[common_parser])

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init-db", parents=[common_parser])
    subparsers.add_parser("check-db", parents=[common_parser])
    subparsers.add_parser("plan-crawl", parents=[common_parser])
    subparsers.add_parser("load-boundaries", parents=[common_parser])
    subparsers.add_parser("fetch-poi", parents=[common_parser])
    subparsers.add_parser("load-income", parents=[common_parser])
    subparsers.add_parser("compute-score", parents=[common_parser])
    pipeline_parser = subparsers.add_parser("pipeline", parents=[common_parser])
    pipeline_parser.add_argument("--yes", action="store_true")
    subparsers.add_parser("generate-figures", parents=[common_parser])
    subparsers.add_parser("dashboard", parents=[common_parser])

    clear_parser = subparsers.add_parser("clear-db", parents=[common_parser])
    clear_parser.add_argument("--yes", action="store_true") #需要加上--yes参数来确认执行

    reset_parser = subparsers.add_parser("reset-db", parents=[common_parser])
    reset_parser.add_argument("--yes", action="store_true") #需要加上--yes参数来确认执行
    return parser


def _require_yes(command: str, yes: bool) -> None:
    """要求 destructive 命令必须显式传入 --yes."""
    if not yes:
        raise SystemExit(f"{command} 是 destructive 命令, 请显式添加 --yes")


def _print_summary(summary: dict) -> None:
    """把 pipeline 返回的 summary 用 key=value 格式打印到终端."""
    for key, value in summary.items():
        print(f"{key}={value}")


def _run_db_command(action) -> None:
    """运行需要数据库连接的命令, 并把 SQLAlchemy 错误转成 CLI 错误."""
    try:
        action()
    except SQLAlchemyError as exc:
        raise SystemExit(f"数据库操作失败: {exc}") from exc


def main() -> None:
    """解析命令行参数并执行对应命令."""
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(args.config)
    engine = create_engine_from_settings(settings.database)
    reporter = ProgressReporter(enabled=settings.progress.enabled)

    command_step_map = {
        "init-db": ["init_db"],
        "check-db": ["check_db"],
        "plan-crawl": ["plan_crawl"],
        "load-boundaries": ["load_boundaries"],
        "fetch-poi": ["fetch_poi"],
        "load-income": ["load_income"],
        "compute-score": ["compute_score"],
        "generate-figures": ["generate_figures"],
        "clear-db": ["clear_db"],
        "reset-db": ["reset_db"],
    }

    destructive_commands = {"clear-db", "reset-db"}

    if args.command in command_step_map:
        if args.command in destructive_commands:
            _require_yes(args.command, args.yes)

        def action() -> None:
            """执行单个 CLI step 并打印 summary."""
            _print_summary(
                execute_pipeline_steps(
                    engine,
                    settings,
                    command_step_map[args.command],
                    reporter=reporter,
                    title=args.command,
                )
            )
        _run_db_command(action)
        return

    if args.command == "pipeline":
        step_ids = resolve_enabled_pipeline_steps(settings)
        destructive_step_ids = {"clear_db", "reset_db"}
        if any(step_id in destructive_step_ids for step_id in step_ids):
            _require_yes("pipeline (contains clear-db/reset-db)", args.yes)

        def action() -> None:
            """执行配置中启用的完整主 pipeline."""
            _print_summary(run_main_pipeline(engine, settings, reporter=reporter))
        _run_db_command(action)
        return

    if args.command == "dashboard":
        from data2001_assignment.visualisation.dashboard import create_dashboard_app

        app = create_dashboard_app(engine, settings)
        app.run(
            host=settings.dashboard.host,
            port=settings.dashboard.port,
            debug=settings.dashboard.debug,
        )
        return

    raise NotImplementedError(f"{args.command} 尚未实现")


if __name__ == "__main__":
    main()
