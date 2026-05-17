import pandas as pd
from data2001.task1_statistics.statistic_result import StatisticResult


def find_indicator(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    matched = df[
        df["description"].str.contains(
            keyword,
            case=False,
            na=False,
            regex=True
        )
    ].copy()

    return matched.sort_values("year")


def longest_streak(values, direction="increase"):
    best = 0
    current = 0

    for i in range(1, len(values)):
        if direction == "increase":
            condition = values[i] > values[i - 1]
        else:
            condition = values[i] < values[i - 1]

        if condition:
            current += 1
            best = max(best, current)
        else:
            current = 0

    return best


def dabi0142_1(df: pd.DataFrame) -> StatisticResult:
    population = find_indicator(df, "Estimated resident population")

    if population.empty:
        return StatisticResult(
            member="dabi0142",
            statistic_id="dabi0142_1",
            title="Population growth rate",
            value=None,
            unit="%",
            description="Population data was not found."
        )

    start_row = population.iloc[0]
    end_row = population.iloc[-1]

    growth_rate = (
        (end_row["value"] - start_row["value"])
        / start_row["value"]
    ) * 100

    return StatisticResult(
        member="dabi0142",
        statistic_id="dabi0142_1",
        title="Population growth rate",
        value=round(growth_rate, 2),
        unit="%",
        description=(
            f"The estimated resident population in NSW grew "
            f"by around {growth_rate:.2f}% between "
            f"{int(start_row['year'])} and "
            f"{int(end_row['year'])}."
        )
    )


def dabi0142_2(df: pd.DataFrame) -> StatisticResult:
    working_age = find_indicator(df, "Working age population")

    if working_age.empty:
        return StatisticResult(
            member="dabi0142",
            statistic_id="dabi0142_2",
            title="Working-age population percentage",
            value=None,
            unit="%",
            description="Working-age population data was not found."
        )

    latest_row = working_age.iloc[-1]

    return StatisticResult(
        member="dabi0142",
        statistic_id="dabi0142_2",
        title="Working-age population percentage",
        value=round(latest_row["value"], 2),
        unit="%",
        description=(
            f"The latest available data shows that "
            f"about {latest_row['value']:.2f}% of people in NSW "
            f"were in the working-age population "
            f"({int(latest_row['year'])})."
        )
    )


def dabi0142_3(df: pd.DataFrame) -> StatisticResult:
    unemployment = find_indicator(df, "Unemployment rate")

    if unemployment.empty:
        return StatisticResult(
            member="dabi0142",
            statistic_id="dabi0142_3",
            title="Largest unemployment rate change",
            value=None,
            unit="percentage points",
            description="Unemployment data was not found."
        )

    unemployment["annual_change"] = unemployment["value"].diff()
    unemployment["abs_annual_change"] = unemployment["annual_change"].abs()

    max_change_row = unemployment.loc[
        unemployment["abs_annual_change"].idxmax()
    ]

    previous_year = int(max_change_row["year"] - 1)

    return StatisticResult(
        member="dabi0142",
        statistic_id="dabi0142_3",
        title="Largest unemployment rate change",
        value=round(max_change_row["annual_change"], 2),
        unit="percentage points",
        description=(
            f"The biggest change in unemployment rate happened "
            f"between {previous_year} and "
            f"{int(max_change_row['year'])}, changing by "
            f"{max_change_row['annual_change']:.2f} percentage points."
        )
    )


def dabi0142_4(df: pd.DataFrame) -> StatisticResult:
    volatility = (
        df
        .groupby("description")["value"]
        .std()
        .dropna()
        .sort_values(ascending=False)
    )

    if volatility.empty:
        return StatisticResult(
            member="dabi0142",
            statistic_id="dabi0142_4",
            title="Most volatile indicator",
            value=None,
            unit="std",
            description="No valid volatility result was found."
        )

    most_volatile_indicator = volatility.index[0]
    most_volatile_value = volatility.iloc[0]

    return StatisticResult(
        member="dabi0142",
        statistic_id="dabi0142_4",
        title="Most volatile indicator",
        value=round(most_volatile_value, 2),
        unit="std",
        description=(
            f"'{most_volatile_indicator}' showed the largest "
            f"variation across years, with a standard deviation "
            f"of {most_volatile_value:.2f}."
        )
    )


def dabi0142_5(df: pd.DataFrame) -> StatisticResult:
    streak_records = []

    for indicator, group in df.groupby("description"):
        group = group.sort_values("year")
        values = group["value"].tolist()

        if len(values) >= 3:
            streak = longest_streak(values, direction="increase")

            streak_records.append({
                "indicator": indicator,
                "streak": streak
            })

    streak_df = pd.DataFrame(streak_records)

    if streak_df.empty:
        return StatisticResult(
            member="dabi0142",
            statistic_id="dabi0142_5",
            title="Longest increase streak",
            value=None,
            unit="years",
            description="No valid streak result was found."
        )

    best_streak = (
        streak_df
        .sort_values("streak", ascending=False)
        .iloc[0]
    )

    return StatisticResult(
        member="dabi0142",
        statistic_id="dabi0142_5",
        title="Longest increase streak",
        value=int(best_streak["streak"]),
        unit="years",
        description=(
            f"'{best_streak['indicator']}' recorded the longest "
            f"continuous upward trend, with "
            f"{int(best_streak['streak'])} consecutive yearly increases."
        )
    )


STATISTICS = [
    dabi0142_1,
    dabi0142_2,
    dabi0142_3,
    dabi0142_4,
    dabi0142_5,
]


def get_dabi0142_statistics(df: pd.DataFrame) -> list[StatisticResult]:
    return [
        statistic(df)
        for statistic in STATISTICS
    ]