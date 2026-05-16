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


#Statistic 1
#Population growth rate

def dabi0142_1(df: pd.DataFrame) -> StatisticResult:

    population = find_indicator(
        df,
        "Estimated resident population.*no"
    )

    start_row = population.iloc[0]
    end_row = population.iloc[-1]

    growth_rate = (
        (end_row["value"] - start_row["value"])
        / start_row["value"]
    ) * 100

    return StatisticResult(
        statistic="Population growth rate",
        value=round(growth_rate, 2),
        description=(
            f"NSW estimated resident population increased "
            f"by {growth_rate:.2f}% from "
            f"{int(start_row['year'])} to "
            f"{int(end_row['year'])}."
        )
    )


#Statistic 2
#Latest working-age population percentage

def dabi0142_2(df: pd.DataFrame) -> StatisticResult:

    working_age = find_indicator(
        df,
        "Working age population.*%"
    )

    latest_row = working_age.iloc[-1]

    return StatisticResult(
        statistic="Latest working-age population percentage",
        value=round(latest_row["value"], 2),
        description=(
            f"In {int(latest_row['year'])}, "
            f"{latest_row['value']:.2f}% of the NSW population "
            f"was aged 15 to 64."
        )
    )


#Statistic 3
#Largest year-to-year unemployment rate change

def dabi0142_3(df: pd.DataFrame) -> StatisticResult:

    unemployment = find_indicator(
        df,
        "Unemployment rate"
    )

    unemployment["annual_change"] = (
        unemployment["value"].diff()
    )

    unemployment["abs_annual_change"] = (
        unemployment["annual_change"].abs()
    )

    max_change_row = unemployment.loc[
        unemployment["abs_annual_change"].idxmax()
    ]

    previous_year = int(max_change_row["year"] - 1)

    return StatisticResult(
        statistic="Largest unemployment rate change",
        value=round(max_change_row["annual_change"], 2),
        description=(
            f"The largest annual unemployment rate change "
            f"was {max_change_row['annual_change']:.2f} percentage "
            f"points between {previous_year} and "
            f"{int(max_change_row['year'])}."
        )
    )


#Statistic 4
#Most volatile indicator

def dabi0142_4(df: pd.DataFrame) -> StatisticResult:

    volatility = (
        df
        .groupby("description")["value"]
        .std()
        .dropna()
        .sort_values(ascending=False)
    )

    most_volatile_indicator = volatility.index[0]
    most_volatile_value = volatility.iloc[0]

    return StatisticResult(
        statistic="Most volatile indicator",
        value=round(most_volatile_value, 2),
        description=(
            f"The most volatile indicator was "
            f"'{most_volatile_indicator}', with a standard "
            f"deviation of {most_volatile_value:.2f}."
        )
    )


#Statistic 5
#Longest continuous increase streak

def dabi0142_5(df: pd.DataFrame) -> StatisticResult:

    streak_records = []

    for indicator, group in df.groupby("description"):

        group = group.sort_values("year")

        values = group["value"].tolist()

        if len(values) >= 3:

            streak = longest_streak(
                values,
                direction="increase"
            )

            streak_records.append({
                "indicator": indicator,
                "streak": streak
            })

    streak_df = pd.DataFrame(streak_records)

    best_streak = (
        streak_df
        .sort_values("streak", ascending=False)
        .iloc[0]
    )

    return StatisticResult(
        statistic="Longest increase streak",
        value=int(best_streak["streak"]),
        description=(
            f"The indicator '{best_streak['indicator']}' "
            f"had the longest continuous increase streak "
            f"with {int(best_streak['streak'])} consecutive "
            f"year-to-year increases."
        )
    )


STATISTICS = [
    dabi0142_1,
    dabi0142_2,
    dabi0142_3,
    dabi0142_4,
    dabi0142_5,
]


def get_dabi0142_statistics(
    df: pd.DataFrame
) -> list[StatisticResult]:

    return [
        statistic(df)
        for statistic in STATISTICS
    ]
