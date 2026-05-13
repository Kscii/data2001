from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class StatisticResult:
    member: str # 你的unikey
    statistic_id: str # 统计函数的id, 按照要求每个人实现5个统计函数, 命名使用"unikey-{函数编号}" 如: xfan0282-1
    title: str # 这个统计项的实际含义
    value: Any # 统计结果的值
    unit: str # 统计结果的单位
    description: str = "" # 统计项的解释文本, 用于在ipynb的notebook中展示, 是可选参数

    def to_dict(self) -> dict:
        return asdict(self)
