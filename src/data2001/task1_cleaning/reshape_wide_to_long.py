import pandas as pd


def reshape_wide_to_long(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()


    year_columns = [col for col in df.columns if col.isdigit()]

    if not year_columns:
        return df

    id_columns = [col for col in df.columns if col not in year_columns]

    long_df = df.melt(
        id_vars=id_columns,
        value_vars=year_columns,
        var_name="year",
        value_name="value"
    )

    long_df["year"] = pd.to_numeric(long_df["year"], errors="coerce")
    long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")

    return long_df
