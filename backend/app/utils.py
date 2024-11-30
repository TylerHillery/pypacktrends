from datetime import date, timedelta
from urllib.parse import urlparse, parse_qs, urlencode

DATE_FORMAT: str = "%Y-%m-%d"


def get_date_n_days_ago(date: date, n_days: int) -> str:
    return (date - timedelta(days=n_days)).strftime(DATE_FORMAT)


def parse_packages(hx_current_url: str) -> set[str]:
    return set(parse_qs(urlparse(hx_current_url).query).get("packages", []))

def generate_push_url(packages: set[str]) -> str:
    return f"?{urlencode({'packages': packages}, doseq=True)}" if packages else "/"