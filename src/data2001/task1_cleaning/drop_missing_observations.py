import pandas as pd


def drop_missing_observations(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "value" not in df.columns:
        return df

    before_rows = len(df)

    df = df.dropna(subset=["value"])

    after_rows = len(df)

    df.attrs["dropped_missing_observation_rows"] = before_rows - after_rows

    return df