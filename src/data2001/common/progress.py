"""Terminal progress helpers for multi-step workflows."""
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WorkflowStep:
    """One executable workflow step."""
    name: str
    action: Callable[[], Any]
    enabled: bool = True


class ProgressReporter:
    """简单终端进度输出；步骤编号由实际启用步骤动态生成."""

    def __init__(self, *, enabled: bool = True) -> None:
        """初始化进度 reporter, 并记录嵌套运行的开始时间."""
        self.enabled = enabled
        self._titles: list[str] = []
        self._started_at: list[float] = []
        self._step_started_at: list[float] = []

    def start(self, title: str) -> None:
        """标记一个多步骤任务开始."""
        self._titles.append(title)
        self._started_at.append(time.perf_counter())
        if self.enabled:
            print(f"{title} started", flush=True)

    def step_start(self, index: int, total: int, name: str) -> None:
        """打印当前步骤编号, 并记录本步骤开始时间."""
        self._step_started_at.append(time.perf_counter())
        if self.enabled:
            print(f"[{index}/{total}] {name}", flush=True)

    def detail(self, message: str) -> None:
        """打印当前步骤的缩进详情信息."""
        if self.enabled:
            print(f"      {message}", flush=True)

    def step_done(self) -> None:
        """标记当前步骤完成, 并输出本步骤耗时."""
        if self.enabled:
            started_at = self._step_started_at.pop() if self._step_started_at else time.perf_counter()
            elapsed = time.perf_counter() - started_at
            print(f"      done in {elapsed:.2f}s", flush=True)
        elif self._step_started_at:
            self._step_started_at.pop()

    def complete(self) -> None:
        """标记当前多步骤任务完成, 并输出总耗时."""
        title = self._titles.pop() if self._titles else "Run"
        started_at = self._started_at.pop() if self._started_at else time.perf_counter()
        if self.enabled:
            elapsed = time.perf_counter() - started_at
            print(f"{title} completed in {elapsed:.2f}s", flush=True)


def run_steps(
    title: str,
    steps: list[WorkflowStep],
    *,
    reporter: ProgressReporter | None = None,
) -> list[Any]:
    """只运行 enabled=True 的步骤, 并自动生成 [当前/总数] 编号."""
    active_steps = [step for step in steps if step.enabled]
    reporter = reporter or ProgressReporter(enabled=False)
    reporter.start(title)
    results: list[Any] = []
    total = len(active_steps)
    for index, step in enumerate(active_steps, start=1):
        reporter.step_start(index, total, step.name)
        results.append(step.action())
        reporter.step_done()
    reporter.complete()
    return results
