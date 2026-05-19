import pandas as pd


def standardise_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise text columns by trimming extra whitespace and replacing empty strings with missing values.

    This cleaning step improves consistency in text-based fields such as measure codes,
    descriptions, and units before reshaping and statistical analysis.
    """
    cleaned_df = df.copy()

    text_columns = cleaned_df.select_dtypes(include="object").columns

    for column in text_columns:
        cleaned_df[column] = cleaned_df[column].astype("string").str.strip()
        cleaned_df[column] = cleaned_df[column].replace("", pd.NA)

    return cleaned_df