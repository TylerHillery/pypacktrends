from datetime import date

from app.utils import get_date_n_days_ago

TEST_DATE = date(2024, 11, 13)


def test_get_date_n_days_ago() -> None:
    result = get_date_n_days_ago(TEST_DATE, 30)
    expected_result = "2024-10-14"
    assert result == expected_result
