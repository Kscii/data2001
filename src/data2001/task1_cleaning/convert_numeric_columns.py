import pandas as pd


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    year_columns = [col for col in df.columns if col.isdigit()]

    for col in year_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df
