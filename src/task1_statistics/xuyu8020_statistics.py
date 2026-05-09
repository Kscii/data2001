import pandas as pd
from src.task1_statistics.statistic_result import StatisticResult

# 返回接口使用StatisticResult中定义的dataclass的格式
# 函数推荐命名为unikey-{统计函数编号}，如: xfan0282-1

def xuyu8020_1(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("xuyu8020_1 is not implemented yet")

def xuyu8020_2(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("xuyu8020_2 is not implemented yet")

def xuyu8020_3(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("xuyu8020_3 is not implemented yet")

def xuyu8020_4(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("xuyu8020_4 is not implemented yet")

def xuyu8020_5(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("xuyu8020_5 is not implemented yet")

STATISTICS = [
    xuyu8020_1,
    xuyu8020_2,
    xuyu8020_3,
    xuyu8020_4,
    xuyu8020_5,
]

def get_xuyu8020_statistics(df: pd.DataFrame) -> list[StatisticResult]:
    return [
        statistic(df)
        for statistic in STATISTICS
    ]
