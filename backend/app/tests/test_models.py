import pytest
import time_machine
from pydantic import ValidationError

from app.models import PYPI_DOWNLOADS_MIN_DATE, TimeRange


def test_time_range_default_value() -> None:
    time_range = TimeRange()
    assert time_range.value == "3months"


def test_time_range_valid_values() -> None:
    valid_values = [
        "1month",
        "3months",
        "6months",
        "1year",
        "2years",
        "5years",
        "allTime",
        "allTimeCumulative",
        "allTimeCumulativeAlignTimeline",
    ]
    for value in valid_values:
        time_range = TimeRange(value=value)  # type: ignore
        assert time_range.value == value


def test_time_range_invalid_value() -> None:
    with pytest.raises(ValidationError):
        TimeRange(value="invalid")  # type: ignore


@time_machine.travel("2024-01-15")
def test_time_range_date_str_calculation() -> None:
    test_cases = [
        ("1month", "2023-12-15"),
        ("3months", "2023-10-15"),
        ("6months", "2023-07-15"),
        ("1year", "2023-01-15"),
        ("2years", "2022-01-15"),
        ("5years", "2019-01-15"),
    ]

    for value, expected_date in test_cases:
        time_range = TimeRange(value=value)  # type: ignore
        assert time_range.date_str == expected_date


@time_machine.travel("2024-01-15")
def test_time_range_all_time_values() -> None:
    all_time_values = ["allTime", "allTimeCumulative", "allTimeCumulativeAlignTimeline"]

    for value in all_time_values:
        time_range = TimeRange(value=value)  # type: ignore
        assert time_range.date_str == PYPI_DOWNLOADS_MIN_DATE
