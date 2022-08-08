from typing import List
from core import IMD
from datetime import datetime
import os


class get_data:
    def __init__(
        self, var_type: str, start_date: str, end_date: str, path: str
    ) -> None:
        self.var_type = var_type
        self.__imd_obj = IMD(self.var_type)
        self.start_date, self.end_date = self.__imd_obj._check_dates(
            datetime.strptime(start_date, "%Y-%m-%d"),
            datetime.strptime(end_date, "%Y-%m-%d"),
        )
        self.download_path = self.__imd_obj._check_path(path)
        self.skipped_download = self.__download()
        self.failed_conversion = []

    def __download(self) -> List:
        # check dates in IMD Availability
        # start date == or > end date
        downloads = map(
            self.__imd_obj._download_grd,
            self.__imd_obj._dtrgen(self.start_date, self.end_date),
            (self.download_path for _ in range((self.end_date-self.start_date).days+1))
        )
        return list(filter(lambda x : x, downloads))


# def get_data(start_date: str, end_date: str, path):
#     """ change str dates into datetime objs
#     check dates in IMD availability
#     check start and end date,
#     if same - directly use IMDGPM class to download single file
#     if diff - call MultiDateData class
#     return the class
#     check if skipped and total are diff if not raise network error
#     """
#     pass
