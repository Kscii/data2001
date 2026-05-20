import pandas as pd


# xfan0282
def extract_unit_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Support both the raw column name and the cleaned column name.
    desc_col = "description" if "description" in df.columns else "Description"
    desc = df[desc_col].astype(str)

    # Extract the unit from a final bracketed suffix, such as "(no.)" or "(years)".
    extracted = desc.str.extract(r"\s*\(([^)]+)\)\s*$", expand=False)
    has_bracket = extracted.notna()

    # Remove the final unit suffix so the description keeps only the measure label.
    stripped_desc = desc.str.replace(r"\s*\([^)]+\)\s*$", "", regex=True).str.strip()

    # Infer units for descriptions that do not have a final bracketed unit.
    no_bracket = ~has_bracket
    inferred = pd.Series(pd.NA, index=df.index, dtype=object)

    # Count-like descriptions use "no." as the unit.
    inferred[no_bracket & desc.str.match(r"^(?:Number of|Total number of)\b", case=False)] = "no."
    # Census count descriptions are also counts.
    inferred[no_bracket & desc.str.match(r"^Census\s*-\s*Count of\b", case=False)] = "no."
    # Percent descriptions can be identified from a leading percent sign.
    inferred[no_bracket & desc.str.startswith("%")] = "%"

    # Prefer extracted units, then fall back to inferred units and normalise aliases.
    unit = extracted.where(has_bracket, inferred)
    unit = unit.replace({"no. of persons": "no."})

    df[desc_col] = stripped_desc.where(has_bracket, desc)
    df["unit"] = unit

    return df
