import pandas as pd
import numpy as np


def validate_and_flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # 找出所有年份列
    year_columns = [
        col
        for col in df.columns
        if str(col).isdigit()
    ]
    #如果没有年份列则直接返回
    if not year_columns:
        return df
    #确保年份列为数值类型
    for col in year_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )
    #使用 IQR 方法标记异常值
    for col in year_columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outlier_column = f"{col}_is_outlier"
        df[outlier_column] = (
            (df[col] < lower_bound) |
            (df[col] > upper_bound)
        )
        #缺失值不算异常值
        df.loc[
            df[col].isna(),
            outlier_column
        ] = False
    #统计每一行异常值数量
    outlier_columns = [
        f"{col}_is_outlier"
        for col in year_columns
    ]
    df["outlier_count"] = (
        df[outlier_columns]
        .sum(axis=1)
    )
    # 是否存在异常值
    df["has_outlier"] = (
        df["outlier_count"] > 0
    )

    return df
