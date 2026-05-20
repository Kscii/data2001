import numpy as np
import pandas as pd


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = df.replace(r"^\s*$", np.nan, regex=True)

    df = df.drop_duplicates()

    year_columns = [col for col in df.columns if col.isdigit()]

    if year_columns:
        df = df.dropna(subset=year_columns, how="all")

    text_columns = [
        "measure_code",
        "parent_description",
        "description"
    ]

    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df
    
