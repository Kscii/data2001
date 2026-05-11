import pandas as pd


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    #找出所有年份列
    year_columns = [col for col in df.columns if col.isdigit()]

    #将年份列转换为数值
    #无法转换的内容会自动变成NaN
    for col in year_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df
