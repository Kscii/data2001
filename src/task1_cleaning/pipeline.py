from pathlib import Path

import pandas as pd

from src.task1_cleaning.clean_column_names import clean_column_names
from src.task1_cleaning.clean_missing_values import clean_missing_values
from src.task1_cleaning.convert_numeric_columns import convert_numeric_columns
from src.task1_cleaning.validate_and_flag_outliers import validate_and_flag_outliers

CLEANING_STEPS = [
    clean_column_names,
    clean_missing_values,
    convert_numeric_columns,
    validate_and_flag_outliers,
]

def run_task1_cleaning(input_csv_path: str, output_csv_path: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(input_csv_path)
    errors: list[str] = []

    for cleaning_step in CLEANING_STEPS:
        step_name = cleaning_step.__name__
        try:
            cleaned_df = cleaning_step(df)
            if cleaned_df is None:
                raise ValueError("Cleaning step returned None")
            if not isinstance(cleaned_df, pd.DataFrame):
                raise TypeError(
                    f"Expected pandas DataFrame, got {type(cleaned_df).__name__}"
                )
        except NotImplementedError as exc:
            continue
        except Exception as exc:
            errors.append(f"{step_name}: {type(exc).__name__}: {exc}")
            continue

        df = cleaned_df

    if errors:
        print("Cleaning pipeline errors:")
        for error in errors:
            print(f"- {error}")

    if output_csv_path:
        output_path = Path(output_csv_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

    return df


if __name__ == "__main__":
    input_csv_path = "data/raw/raw_data.csv"
    output_csv_path = "data/processed/cleaned_data.csv"
    cleaned_df = run_task1_cleaning(input_csv_path, output_csv_path)