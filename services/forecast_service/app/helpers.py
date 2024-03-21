from pydantic import BaseModel
from typing import Union
import datetime
import pandas as pd


class ForecastRequest(BaseModel):
    store_id: str
    product_name: str
    begin_date: Union[str, None] = None
    end_date: Union[str, None] = None


def create_forecast_index(begin_date: str = None, end_date: str = None):
    if begin_date is None:
        begin_date = datetime.datetime.now().replace(tzinfo=None)
    else:
        begin_date = datetime.datetime.strptime(
            begin_date, "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=None)

    if end_date is None:
        end_date = begin_date + datetime.timedelta(days=7)
    else:
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=None
        )

    forecast_index = pd.date_range(start=begin_date, end=end_date, freq="D")
    return pd.DataFrame({"ds": forecast_index})
