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

    def __init__(self, *, enabled: bool = True) -> None:
        self.enabled = enabled
        self._titles: list[str] = []
        self._started_at: list[float] = []
        self._step_started_at: list[float] = []

    def start(self, title: str) -> None:
        self._titles.append(title)
        self._started_at.append(time.perf_counter())
        if self.enabled:
            print(f"{title} started", flush=True)

    def step_start(self, index: int, total: int, name: str) -> None:
        self._step_started_at.append(time.perf_counter())
        if self.enabled:
            print(f"[{index}/{total}] {name}", flush=True)

    def detail(self, message: str) -> None:
        if self.enabled:
            print(f"      {message}", flush=True)

    def step_done(self) -> None:
        if self.enabled:
            started_at = self._step_started_at.pop() if self._step_started_at else time.perf_counter()
            elapsed = time.perf_counter() - started_at
            print(f"      done in {elapsed:.2f}s", flush=True)
        elif self._step_started_at:
            self._step_started_at.pop()

    def complete(self) -> None:
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
