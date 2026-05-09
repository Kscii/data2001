import pandas as pd
from src.task1_statistics.statistic_result import StatisticResult

# 返回接口使用StatisticResult中定义的dataclass的格式
# 函数推荐命名为unikey-{统计函数编号}，如: xfan0282-1

def xfan0282_1(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("xfan0282_1 is not implemented yet")

def xfan0282_2(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("xfan0282_2 is not implemented yet")

def xfan0282_3(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("xfan0282_3 is not implemented yet")

def xfan0282_4(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("xfan0282_4 is not implemented yet")

def xfan0282_5(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("xfan0282_5 is not implemented yet")

STATISTICS = [
    xfan0282_1,
    xfan0282_2,
    xfan0282_3,
    xfan0282_4,
    xfan0282_5,
]

def get_xfan0282_statistics(df: pd.DataFrame) -> list[StatisticResult]:
    return [
        statistic(df)
        for statistic in STATISTICS
    ]
