"""Shared lightweight type aliases."""
from __future__ import annotations

from typing import TypeAlias

SummaryValue: TypeAlias = int | float | str
StepSummary: TypeAlias = dict[str, SummaryValue]
