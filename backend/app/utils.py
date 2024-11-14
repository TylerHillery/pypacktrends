from datetime import date, timedelta

DATE_FORMAT: str = "%Y-%m-%d"


def get_date_n_days_ago(date: date, n_days: int) -> str:
    return (date - timedelta(days=n_days)).strftime(DATE_FORMAT)
