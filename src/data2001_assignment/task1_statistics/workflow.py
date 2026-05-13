from pathlib import Path
from typing import cast

import pandas as pd

from data2001_assignment.task1_statistics import (
    dabi0142_statistics,
    jzho0172_statistics,
    xfan0282_statistics,
    xuyu8020_statistics,
)
from data2001_assignment.task1_statistics.statistic_result import StatisticResult

EXPECTED_COLUMNS = [
    "member", # 你的unikey
    "statistic_id", # 统计函数的id, 按照要求每个人实现5个统计函数, 命名使用"unikey-{函数编号}" 如: xfan0282-1
    "title", # 这个统计项的实际含义
    "value", # 统计结果的值
    "unit", # 统计结果的单位
    "description", # 统计项的解释文本, 用于在ipynb的notebook中展示, 是可选参数
]

STATISTIC_FUNCTIONS = []
STATISTIC_FUNCTIONS.extend(dabi0142_statistics.STATISTICS)
STATISTIC_FUNCTIONS.extend(xuyu8020_statistics.STATISTICS)
STATISTIC_FUNCTIONS.extend(jzho0172_statistics.STATISTICS)
STATISTIC_FUNCTIONS.extend(xfan0282_statistics.STATISTICS)

def validate_result(result: StatisticResult) -> None:
    if not isinstance(result, StatisticResult):
        raise TypeError(
            f"Expected StatisticResult, got {type(result).__name__}"
        )
    if not result.member:
        raise ValueError("Missing member")
    if not result.statistic_id:
        raise ValueError("Missing statistic_id")
    if not result.title:
        raise ValueError(f"{result.statistic_id} is missing title")
    if result.value is None:
        raise ValueError(f"{result.statistic_id} is missing value")

def run_all_task1_statistics(df: pd.DataFrame) -> pd.DataFrame:
    results: list[StatisticResult] = []
    errors: list[str] = []

    for statistic_function in STATISTIC_FUNCTIONS:
        function_name = statistic_function.__name__
        try:
            result = statistic_function(df)
            validate_result(result)
        except NotImplementedError as exc:
            continue
        except Exception as exc:
            errors.append(f"{function_name}: {type(exc).__name__}: {exc}")
            continue

        results.append(result)

    if errors:
        print("Statistics workflow errors:")
        for error in errors:
            print(f"- {error}")

    statistics_df = pd.DataFrame(
        [result.to_dict() for result in results],
        columns=EXPECTED_COLUMNS,
    )
    return cast(pd.DataFrame, statistics_df.loc[:, EXPECTED_COLUMNS])

if __name__ == "__main__":
    input_csv = Path("data/processed/cleaned_data.csv")
    output_csv = Path("data/statistics/statistics_output.csv")
    df = pd.read_csv(input_csv)
    statistics_df = run_all_task1_statistics(df)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    statistics_df.to_csv(output_csv, index=False)
