from typing import List
from core import IMD
from datetime import datetime
import os


class get_data:
    __IMDPARAMS = ('raingpm','tmax','tmin','rain','tmaxone','tminone')
    def __init__(self, parameter: str, start_date: str, end_date: str, path: str) -> None:
        if parameter in get_data.__IMDPARAMS:
            self.param = parameter
        else:
            raise ValueError(f'{parameter} is not available in IMD. {get_data.__IMDPARAMS}')
        self.__imd = IMD(self.param)
        self.start_date, self.end_date = self.__imd._check_dates(start_date, end_date)
        self.download_path = self.__imd._check_path(path)
        self.total_days = (self.end_date-self.start_date).days+1
        self.skipped_download = self.__download()
        self.failed_conversion = []

    def __download(self) -> List:
        downloads = map(
            self.__imd._download_grd,
            self.__imd._dtrgen(self.start_date, self.end_date),
            (self.download_path for _ in range(self.total_days))
        )
        return list(filter(lambda x : x, downloads))
