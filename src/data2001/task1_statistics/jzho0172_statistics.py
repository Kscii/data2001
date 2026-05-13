import pandas as pd
from data2001.task1_statistics.statistic_result import StatisticResult

# 返回接口使用StatisticResult中定义的dataclass的格式
# 函数推荐命名为unikey-{统计函数编号}，如: xfan0282-1

def jzho0172_1(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("jzho0172_1 is not implemented yet")

def jzho0172_2(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("jzho0172_2 is not implemented yet")

def jzho0172_3(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("jzho0172_3 is not implemented yet")

def jzho0172_4(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("jzho0172_4 is not implemented yet")

def jzho0172_5(df: pd.DataFrame) -> StatisticResult:
    raise NotImplementedError("jzho0172_5 is not implemented yet")

STATISTICS = [
    jzho0172_1,
    jzho0172_2,
    jzho0172_3,
    jzho0172_4,
    jzho0172_5,
]

def get_jzho0172_statistics(df: pd.DataFrame) -> list[StatisticResult]:
    return [
        statistic(df)
        for statistic in STATISTICS
    ]
