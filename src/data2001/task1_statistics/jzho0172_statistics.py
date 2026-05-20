import pandas as pd
from data2001.task1_statistics.statistic_result import StatisticResult


MEMBER = "jzho0172"


def _value(df: pd.DataFrame, measure_code: str, year: int) -> float:
    """Read one measure/year value from the shared cleaned long dataframe."""
    required_columns = {"measure_code", "year", "value"}
    missing = required_columns.difference(df.columns)
    if missing:
        raise KeyError(f"Task 1 cleaned data is missing columns: {sorted(missing)}")

    rows = df[
        (df["measure_code"] == measure_code)
        & (pd.to_numeric(df["year"], errors="coerce") == year)
    ]
    if rows.empty:
        raise KeyError(f"Missing value for {measure_code} in {year}")

    value = pd.to_numeric(rows.iloc[0]["value"], errors="coerce")

    if pd.isna(value):
        raise ValueError(f"Value for {measure_code} in {year} is empty")
    return float(value)


def _percentage_change(start: float, end: float) -> float:
    if start == 0:
        raise ZeroDivisionError("Cannot calculate percentage change from zero")
    return (end - start) / start * 100


def _percentage_point_change(start: float, end: float) -> float:
    return end - start


def jzho0172_1(df: pd.DataFrame) -> StatisticResult:
    population_2019 = _value(df, "ERP_P_20", 2019)
    population_2024 = _value(df, "ERP_P_20", 2024)
    growth = _percentage_change(population_2019, population_2024)

    return StatisticResult(
        member=MEMBER,
        statistic_id="jzho0172-1",
        title="Estimated resident population growth, 2019-2024",
        value=round(growth, 2),
        unit="percent",
        description=(
            f"Estimated resident population increased from {population_2019:,.0f} in 2019 "
            f"to {population_2024:,.0f} in 2024, representing growth of {growth:.2f}%."
        ),
    )


def jzho0172_2(df: pd.DataFrame) -> StatisticResult:
    density_2019 = _value(df, "ERP_21", 2019)
    density_2024 = _value(df, "ERP_21", 2024)
    density_change = _percentage_point_change(density_2019, density_2024)

    return StatisticResult(
        member=MEMBER,
        statistic_id="jzho0172-2",
        title="Population density change, 2019-2024",
        value=round(density_change, 2),
        unit="persons/km2",
        description=(
            f"Population density changed from {density_2019:.1f} persons/km2 in 2019 "
            f"to {density_2024:.1f} persons/km2 in 2024, a change of {density_change:.2f} persons/km2."
        ),
    )


def jzho0172_3(df: pd.DataFrame) -> StatisticResult:
    female_population = _value(df, "ERP_F_20", 2024)
    total_population = _value(df, "ERP_P_20", 2024)
    female_share = female_population / total_population * 100

    return StatisticResult(
        member=MEMBER,
        statistic_id="jzho0172-3",
        title="Female share of estimated resident population, 2024",
        value=round(female_share, 2),
        unit="percent",
        description=(
            f"In 2024, females accounted for {female_share:.2f}% of the estimated resident population "
            f"({female_population:,.0f} out of {total_population:,.0f} people)."
        ),
    )


def jzho0172_4(df: pd.DataFrame) -> StatisticResult:
    male_population = _value(df, "ERP_M_20", 2024)
    female_population = _value(df, "ERP_F_20", 2024)
    gender_gap = female_population - male_population

    return StatisticResult(
        member=MEMBER,
        statistic_id="jzho0172-4",
        title="Female-male population gap, 2024",
        value=round(gender_gap, 2),
        unit="people",
        description=(
            f"In 2024, the female population was {female_population:,.0f}, compared with "
            f"{male_population:,.0f} males. The female-male population gap was {gender_gap:,.0f} people."
        ),
    )


def jzho0172_5(df: pd.DataFrame) -> StatisticResult:
    median_age_male_2019 = _value(df, "ERP_19", 2019)
    median_age_male_2024 = _value(df, "ERP_19", 2024)
    age_change = _percentage_point_change(median_age_male_2019, median_age_male_2024)

    return StatisticResult(
        member=MEMBER,
        statistic_id="jzho0172-5",
        title="Median male age change, 2019-2024",
        value=round(age_change, 2),
        unit="years",
        description=(
            f"The median age of males changed from {median_age_male_2019:.1f} years in 2019 "
            f"to {median_age_male_2024:.1f} years in 2024, a change of {age_change:.2f} years."
        ),
    )


STATISTICS = [
    jzho0172_1,
    jzho0172_2,
    jzho0172_3,
    jzho0172_4,
    jzho0172_5,
]
