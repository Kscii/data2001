import pandas as pd

from data2001.task1_statistics.statistic_result import StatisticResult


MEMBER = "xuyu8020"


def _measure_code_column(df: pd.DataFrame) -> str:
    if "measure_code" in df.columns:
        return "measure_code"

    if "Measure Code" in df.columns:
        return "Measure Code"

    raise KeyError("Task 1 data is missing a measure code column")


def _value(df: pd.DataFrame, measure_code: str, year: int) -> float:
    code_column = _measure_code_column(df)

    if {"year", "value"}.issubset(df.columns):
        years = pd.to_numeric(df["year"], errors="coerce")
        rows = df[
            (df[code_column] == measure_code)
            & (years == year)
        ]

        if rows.empty:
            raise KeyError(f"Missing value for {measure_code} in {year}")

        value = pd.to_numeric(
            rows.iloc[0]["value"],
            errors="coerce"
        )

    else:
        year_column = str(year)

        if year_column not in df.columns:
            raise KeyError(f"Task 1 data is missing year column {year_column}")

        rows = df[df[code_column] == measure_code]

        if rows.empty:
            raise KeyError(f"Missing measure {measure_code}")

        value = pd.to_numeric(
            rows.iloc[0][year_column],
            errors="coerce"
        )

    if pd.isna(value):
        raise ValueError(f"Value for {measure_code} in {year} is empty")

    return float(value)


def _ratio_percent(numerator: float, denominator: float) -> float:
    if denominator == 0:
        raise ZeroDivisionError("Cannot calculate percentage with zero denominator")

    return numerator / denominator * 100


def _growth_percent(start: float, end: float) -> float:
    if start == 0:
        raise ZeroDivisionError("Cannot calculate growth rate from zero starting value")

    return (end - start) / start * 100


def xuyu8020_1(df: pd.DataFrame) -> StatisticResult:
    total_population = _value(df, "ERP_P_20", 2024)
    working_age_population = _value(df, "ERP_18", 2024)

    dependent_population = total_population - working_age_population
    dependency_ratio = _ratio_percent(
        dependent_population,
        working_age_population
    )

    return StatisticResult(
        member=MEMBER,
        statistic_id="xuyu8020-1",
        title="Age dependency ratio, 2024",
        value=round(dependency_ratio, 2),
        unit="dependents per 100 working-age persons",
        description=(
            f"In 2024, NSW had about {dependency_ratio:.2f} people aged outside "
            f"15-64 for every 100 people of working age. This statistic compares "
            f"the estimated resident population with the working-age population."
        ),
    )


def xuyu8020_2(df: pd.DataFrame) -> StatisticResult:
    male_population = _value(df, "ERP_M_20", 2024)
    female_population = _value(df, "ERP_F_20", 2024)

    sex_ratio = _ratio_percent(
        male_population,
        female_population
    )

    return StatisticResult(
        member=MEMBER,
        statistic_id="xuyu8020-2",
        title="Sex ratio, 2024",
        value=round(sex_ratio, 2),
        unit="males per 100 females",
        description=(
            f"In 2024, NSW had approximately {sex_ratio:.2f} males per 100 "
            f"females. This indicates that the female population was slightly "
            f"larger than the male population."
        ),
    )


def xuyu8020_3(df: pd.DataFrame) -> StatisticResult:
    median_income_2018 = _value(df, "INCOME_17", 2018)
    median_income_2022 = _value(df, "INCOME_17", 2022)

    income_growth = _growth_percent(
        median_income_2018,
        median_income_2022
    )

    return StatisticResult(
        member=MEMBER,
        statistic_id="xuyu8020-3",
        title="Median total income growth, 2018-2022",
        value=round(income_growth, 2),
        unit="%",
        description=(
            f"Median total income excluding government pensions and allowances "
            f"increased from ${median_income_2018:,.0f} in 2018 to "
            f"${median_income_2022:,.0f} in 2022. This represents a growth rate "
            f"of {income_growth:.2f}%."
        ),
    )


def xuyu8020_4(df: pd.DataFrame) -> StatisticResult:
    median_income = _value(df, "INCOME_17", 2022)
    mean_income = _value(df, "INCOME_36", 2022)

    mean_median_gap = _growth_percent(
        median_income,
        mean_income
    )

    return StatisticResult(
        member=MEMBER,
        statistic_id="xuyu8020-4",
        title="Mean-to-median total income gap, 2022",
        value=round(mean_median_gap, 2),
        unit="% above median",
        description=(
            f"In 2022, mean total income (${mean_income:,.0f}) was "
            f"{mean_median_gap:.2f}% higher than median total income "
            f"(${median_income:,.0f}). This provides a simple indication that "
            f"the income distribution was right-skewed."
        ),
    )


def xuyu8020_5(df: pd.DataFrame) -> StatisticResult:
    business_entries = _value(df, "CABEE_10", 2024)
    business_exits = _value(df, "CABEE_15", 2024)
    total_businesses = _value(df, "CABEE_5", 2024)

    net_entry_rate = _ratio_percent(
        business_entries - business_exits,
        total_businesses
    )

    return StatisticResult(
        member=MEMBER,
        statistic_id="xuyu8020-5",
        title="Business net entry rate, 2024",
        value=round(net_entry_rate, 2),
        unit="% of total businesses",
        description=(
            f"In 2024, NSW recorded {business_entries:,.0f} business entries "
            f"and {business_exits:,.0f} business exits. The net increase was "
            f"equivalent to {net_entry_rate:.2f}% of the total number of "
            f"businesses."
        ),
    )


STATISTICS = [
    xuyu8020_1,
    xuyu8020_2,
    xuyu8020_3,
    xuyu8020_4,
    xuyu8020_5,
]


def get_xuyu8020_statistics(df: pd.DataFrame) -> list[StatisticResult]:
    return [
        statistic(df)
        for statistic in STATISTICS
    ]