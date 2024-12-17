from app.models import QueryParams, TimeRange
from app.utils import (
    generate_hx_push_url,
    parse_query_params,
    start_of_week,
)


def test_start_of_week() -> None:
    result = start_of_week("2024-12-06")
    expected_result = "2024-12-02"
    assert result == expected_result


def test_parse_query_params() -> None:
    url = "https://localhost:8000/?packages=duckdb&packages=pandas&time_range=1month"
    result = parse_query_params(url)

    expected_result = QueryParams(
        packages=["duckdb", "pandas"], time_range=TimeRange(value="1month")
    )
    assert result.packages == expected_result.packages
    assert result.time_range.value == expected_result.time_range.value


def test_generate_hx_push_url_packages() -> None:
    result = generate_hx_push_url(
        QueryParams(packages=["duckdb", "pandas"], time_range=TimeRange())
    )
    expected_result = "?packages=duckdb&packages=pandas&time_range=3months"
    assert result == expected_result


def test_generate_hx_push_url_no_packages() -> None:
    result = generate_hx_push_url(QueryParams(packages=[], time_range=TimeRange()))
    expected_result = "/"
    assert result == expected_result
