from re import I
from core import IMD
from datetime import datetime
import os


class get_data:
    def __init__(self, type: str, start_date: str, end_date: str, path: str) -> None:
        self.var_type = type
        self.__imd_obj = IMD(type)
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.download_path = os.path.normpath(path)
        self.__check_path(self.download_path)
        self.skipped_download = []
        self.failed_conversion = []

    def __check_path(self, path: str) -> None:
        if not os.path.isdir(path):
            raise OSError(f"{path} does not exist.")

    def __download(self):
        # check dates in IMD Availability
        # start date == or > end date
        pass

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
