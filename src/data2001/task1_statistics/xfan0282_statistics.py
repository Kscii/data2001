import pandas as pd

from data2001.task1_statistics.statistic_result import StatisticResult

# Each statistic returns the shared StatisticResult dataclass.
# Function names follow the member/statistic id pattern, for example xfan0282_1.


MEMBER = "xfan0282"


def _value(df: pd.DataFrame, measure_code: str, year: int) -> float:
    """Read one measure/year value from the shared cleaned long dataframe."""
    # The statistics depend on the shared long-format cleaning output.
    required_columns = {"measure_code", "year", "value"}
    missing = required_columns.difference(df.columns)
    if missing:
        raise KeyError(f"Task 1 cleaned data is missing columns: {sorted(missing)}")

    # Match one measure code and one year, then coerce the stored value to numeric.
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


def _share(df: pd.DataFrame, numerator_code: str, denominator_code: str, year: int) -> float:
    # Convert two count measures into a percentage share for the selected year.
    return _value(df, numerator_code, year) / _value(df, denominator_code, year) * 100


def _percentage_point_change(start: float, end: float) -> float:
    return end - start


def _ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        raise ZeroDivisionError("Cannot calculate ratio with zero denominator")
    return numerator / denominator


def xfan0282_1(df: pd.DataFrame) -> StatisticResult:
    # Compare apartment and separate-house shares to describe dwelling structure change.
    separate_2011 = _share(df, "DWELL_2", "DWELL_7", 2011)
    separate_2021 = _share(df, "DWELL_2", "DWELL_7", 2021)
    apartment_2011 = _share(df, "DWELL_4", "DWELL_7", 2011)
    apartment_2021 = _share(df, "DWELL_4", "DWELL_7", 2021)

    apartment_change = _percentage_point_change(apartment_2011, apartment_2021)
    separate_change = _percentage_point_change(separate_2011, separate_2021)

    return StatisticResult(
        member=MEMBER,
        statistic_id="xfan0282-1",
        title="Apartment share increase among occupied private dwellings, 2011-2021",
        value=round(apartment_change, 2),
        unit="percentage points",
        description=(
            f"Apartment share increased {apartment_change:.2f}pp to {apartment_2021:.2f}% (2011-2021), "
            "indicating residential structure shift."
        ),
    )

def xfan0282_2(df: pd.DataFrame) -> StatisticResult:
    # Measure how much the work-from-home share grew between the two census years.
    wfh_2016 = _share(df, "WORK_TRAV_14", "WORK_TRAV_17", 2016)
    wfh_2021 = _share(df, "WORK_TRAV_14", "WORK_TRAV_17", 2021)
    growth_ratio = _ratio(wfh_2021, wfh_2016)

    return StatisticResult(
        member=MEMBER,
        statistic_id="xfan0282-2",
        title="Work-from-home share growth, 2016-2021",
        value=round(growth_ratio, 2),
        unit="times",
        description=(
            f"Work-from-home share grew {growth_ratio:.2f}x from {wfh_2016:.2f}% to {wfh_2021:.2f}% (2016-2021)."
        ),
    )

def xfan0282_3(df: pd.DataFrame) -> StatisticResult:
    # Check whether public transport commuting fell alongside the work-from-home rise.
    public_transport_2016 = _share(df, "WORK_TRAV_23", "WORK_TRAV_17", 2016)
    public_transport_2021 = _share(df, "WORK_TRAV_23", "WORK_TRAV_17", 2021)
    drop = public_transport_2016 - public_transport_2021

    return StatisticResult(
        member=MEMBER,
        statistic_id="xfan0282-3",
        title="Public transport commute share drop, 2016-2021",
        value=round(drop, 2),
        unit="percentage points",
        description=(
            f"Public transport commute share dropped {drop:.2f}pp from {public_transport_2016:.2f}% to {public_transport_2021:.2f}% (2016-2021)."
        ),
    )

def xfan0282_4(df: pd.DataFrame) -> StatisticResult:
    # Compare occupation-specific commute distances to show hidden variation.
    occupation_commute_codes = {
        "managers": "COMMUTE_10",
        "professionals": "COMMUTE_11",
        "technicians/trades": "COMMUTE_12",
        "community/service": "COMMUTE_13",
        "machinery/drivers": "COMMUTE_16",
        "labourers": "COMMUTE_17",
    }
    commute_by_occupation = {
        occupation: _value(df, measure_code, 2016)
        for occupation, measure_code in occupation_commute_codes.items()
    }
    longest_occupation = max(commute_by_occupation, key=commute_by_occupation.get)
    shortest_occupation = min(commute_by_occupation, key=commute_by_occupation.get)
    gap = commute_by_occupation[longest_occupation] - commute_by_occupation[shortest_occupation]

    return StatisticResult(
        member=MEMBER,
        statistic_id="xfan0282-4",
        title="Occupation commute distance gap, 2016",
        value=round(gap, 2),
        unit="km",
        description=(
            f"Commute distance gap in 2016: {gap:.1f} km (range {commute_by_occupation[shortest_occupation]:.1f}-{commute_by_occupation[longest_occupation]:.1f} km across occupations)."
        ),
    )

def xfan0282_5(df: pd.DataFrame) -> StatisticResult:
    # Compare renter and mortgage-holder stress to summarise housing pressure.
    rent_stress = _value(df, "STRESS_17", 2021)
    mortgage_stress = _value(df, "STRESS_15", 2021)
    stress_ratio = _ratio(rent_stress, mortgage_stress)

    return StatisticResult(
        member=MEMBER,
        statistic_id="xfan0282-5",
        title="Rent stress relative to mortgage stress, 2021",
        value=round(stress_ratio, 2),
        unit="times",
        description=(
            f"Rent stress ({rent_stress:.1f}%) is {stress_ratio:.2f}x mortgage stress ({mortgage_stress:.1f}%) in 2021."
        ),
    )

STATISTICS = [
    xfan0282_1,
    xfan0282_2,
    xfan0282_3,
    xfan0282_4,
    xfan0282_5,
]
