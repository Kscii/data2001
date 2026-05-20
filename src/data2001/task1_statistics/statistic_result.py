from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class StatisticResult:
    member: str
    statistic_id: str
    title: str
    value: Any
    unit: str
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
