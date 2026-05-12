"""Pipeline 配置解析工具, 负责校验 enabled steps 和 CLI step id."""
from __future__ import annotations

from data2001_assignment.config import Settings


class PipelinePlanError(ValueError):
    """当 YAML 中的 pipeline step 配置无效时抛出."""


def step_id_to_command(step_id: str) -> str:
    """把内部 step_id 转成 CLI 子命令写法."""
    return step_id.replace("_", "-")


def command_to_step_id(command: str) -> str:
    """把 CLI 子命令写法转成内部 step_id."""
    return command.replace("-", "_")


def resolve_enabled_pipeline_steps(settings: Settings) -> list[str]:
    """读取并校验配置中启用的 pipeline steps."""
    available = settings.pipeline.steps_available
    enabled = settings.pipeline.steps_enabled

    if not available:
        raise PipelinePlanError("pipeline.steps_available 不能为空")
    if not enabled:
        raise PipelinePlanError("pipeline.steps_enabled 不能为空")

    unknown = sorted({step_id for step_id in enabled if step_id not in available})
    if unknown:
        raise PipelinePlanError(
            f"pipeline.steps_enabled 包含未知步骤: {unknown}; "
            f"steps_available={available}"
        )

    duplicated = sorted({step_id for step_id in enabled if enabled.count(step_id) > 1})
    if duplicated:
        raise PipelinePlanError(f"pipeline.steps_enabled 存在重复步骤: {duplicated}")

    return enabled
