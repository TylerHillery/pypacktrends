from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, computed_field

TIME_RANGE_MAPPING = {
    "1month": dict(months=1),
    "3months": dict(months=3),
    "6months": dict(months=6),
    "1year": dict(years=1),
    "2years": dict(years=2),
    "5years": dict(years=5),
}

PYPI_DOWNLOADS_MIN_DATE = "2016-01-01"

TimeRangeValidValues = Literal[
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


class TimeRange(BaseModel):
    value: TimeRangeValidValues = "3months"

    @computed_field  # type: ignore
    @property
    def date_str(self) -> str:
        if self.value in [
            "allTime",
            "allTimeCumulative",
            "allTimeCumulativeAlignTimeline",
        ]:
            return PYPI_DOWNLOADS_MIN_DATE

        return (
            (
                datetime.now(ZoneInfo("UTC"))
                - relativedelta(**(TIME_RANGE_MAPPING[self.value]))  # type: ignore
            )
            .date()
            .isoformat()
        )


class QueryParams(BaseModel):
    packages: list[str] = []
    time_range: TimeRange = TimeRange(value="3months")
    show_percentage: Literal["on"] | None = None
    error: str | None = None
