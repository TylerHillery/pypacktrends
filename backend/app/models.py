from datetime import datetime 
from zoneinfo import ZoneInfo
from pydantic import BaseModel, computed_field
from typing import Literal 

from dateutil.relativedelta import relativedelta

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
            "1month": {
                "months": 1
            },
            "3months": {
                "months": 3
            },
            "6months": {
                "months": 6
            },
            "1year": {
                "years": 1
            },
            "2years": {
                "years": 2
            },
            "5years": {
                "years": 5
            },
        }
        return (datetime.now(ZoneInfo("UTC")) - relativedelta(**time_range_mapping[self.value])).date().isoformat()

    @computed_field
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
    
    