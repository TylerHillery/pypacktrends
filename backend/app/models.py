from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, computed_field

PYPI_DOWNLOADS_MIN_DATE = "2015-12-27"

TimeRangeValue = Literal[
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


class TimeRangeModel(BaseModel):
    value: TimeRangeValue = "1month"

    def _get_relative_date_str(self, time_range: TimeRangeValue) -> str:
        time_range_mapping = {
            "1month": relativedelta(months=1),
            "3months": relativedelta(months=3),
            "6months": relativedelta(months=6),
            "1year": relativedelta(years=1),
            "2years": relativedelta(years=2),
            "5years": relativedelta(years=5),
        }
        return (
            (datetime.now(ZoneInfo("UTC")) - time_range_mapping[self.value])
            .date()
            .isoformat()
        )

    @computed_field  # type: ignore
    @property
    def date(self) -> str:
        match self.value:
            case "1month":
                return self._get_relative_date_str(self.value)
            case "3months":
                return self._get_relative_date_str(self.value)
            case "6months":
                return self._get_relative_date_str(self.value)
            case "1year":
                return self._get_relative_date_str(self.value)
            case "2years":
                return self._get_relative_date_str(self.value)
            case "5years":
                return self._get_relative_date_str(self.value)
            case "allTime":
                return PYPI_DOWNLOADS_MIN_DATE
            case "allTimeCumulative":
                return PYPI_DOWNLOADS_MIN_DATE
            case "allTimeCumulativeAlignTimeline":
                return PYPI_DOWNLOADS_MIN_DATE
            case _:
                raise ValueError()
