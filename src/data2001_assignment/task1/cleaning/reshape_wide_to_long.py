import pandas as pd


def reshape_wide_to_long(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    #找出所有年份列

    year_columns = [col for col in df.columns if col.isdigit()]

    # 如果没有年份列则直接返回原数据
    if not year_columns:
        return df

    #保留非年份列作为ID列
    id_columns = [col for col in df.columns if col not in year_columns]

    #将wide format转换为long format
    long_df = df.melt(
        id_vars=id_columns,
        value_vars=year_columns,
        var_name="year",
        value_name="value"
    )

    #将year和value转成数值类型
    long_df["year"] = pd.to_numeric(long_df["year"], errors="coerce")
    long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")

    return long_df
