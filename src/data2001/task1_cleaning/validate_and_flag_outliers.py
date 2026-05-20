import pandas as pd
import numpy as np


def validate_and_flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    year_columns = [
        col
        for col in df.columns
        if str(col).isdigit()
    ]
    if not year_columns:
        return df
    for col in year_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )
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
        df.loc[
            df[col].isna(),
            outlier_column
        ] = False
    outlier_columns = [
        f"{col}_is_outlier"
        for col in year_columns
    ]
    df["outlier_count"] = (
        df[outlier_columns]
        .sum(axis=1)
    )
    df["has_outlier"] = (
        df["outlier_count"] > 0
    )

    return df
