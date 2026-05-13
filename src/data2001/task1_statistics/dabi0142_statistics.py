import pandas as pd
from data2001.task1_statistics.statistic_result import StatisticResult

# 返回接口使用StatisticResult中定义的dataclass的格式
# 函数推荐命名为unikey-{统计函数编号}，如: xfan0282-1

def dabi0142_1(df: pd.DataFrame) -> StatisticResult: 
    raise NotImplementedError("dabi0142_1 is not implemented yet")

def dabi0142_2(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("dabi0142_2 is not implemented yet")

def dabi0142_3(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("dabi0142_3 is not implemented yet")

def dabi0142_4(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("dabi0142_4 is not implemented yet")

def dabi0142_5(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("dabi0142_5 is not implemented yet")

STATISTICS = [
    dabi0142_1,
    dabi0142_2,
    dabi0142_3,
    dabi0142_4,
    dabi0142_5,
]

def get_dabi0142_statistics(df: pd.DataFrame) -> list[StatisticResult]:
    return [
        statistic(df)
        for statistic in STATISTICS
    ]
