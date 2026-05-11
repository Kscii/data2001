import pandas as pd


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 清理列名方便后续Python处理
    df.columns = (
        df.columns
        .str.strip()                     #去除前后空格
        .str.lower()                    #转成小写
        .str.replace(" ", "_")          #空格替换为下划线
        .str.replace(r"[^\w]", "", regex=True)  #删除特殊符号
    )

    return df
