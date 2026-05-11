import numpy as np
import pandas as pd


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    #将空字符串替换为缺失值
    df = df.replace(r"^\s*$", np.nan, regex=True)

    #删除重复行
    df = df.drop_duplicates()

    #找出年份列
    year_columns = [col for col in df.columns if col.isdigit()]

    #如果某一行所有年份数据都为空，则删除该行
    if year_columns:
        df = df.dropna(subset=year_columns, how="all")

    #需要清理文本空格的重要列
    text_columns = [
        "measure_code",
        "parent_description",
        "description"
    ]

    #去除文本列中的前后空格
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df
    
