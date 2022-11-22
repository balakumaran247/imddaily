"""Main file of the imddaily package while organizes all the functionalities like
download and convert the real time data from IMD.
"""
from typing import List
from .core import IMD
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import rasterio
import numpy as np

__version__ = "0.3.0"


class get_data:
    """Main class of imddaily package which downloads the grd data from IMD upon
    initialization and contains the methods for conversion of the downloaded data
    to desired formats.

    Args:
        parameter (str): one of 'raingpm','tmax','tmin','rain','tmaxone','tminone'
        start_date (str): start date to get data
        end_date (str): end date for data
        path (str): directory path to save the downloaded data
        quiet (bool, optional): when True does not display Progress Bar. Defaults to False.

    Raises:
        ValueError: provided parameter is not recognized
        OSError: path does not exist
        ValueError: incorrect Date Format or Data for date not available
    """

    __IMDPARAMS = ("raingpm", "tmax", "tmin", "rain", "tmaxone", "tminone")

    def __init__(
        self,
        parameter: str,
        start_date: str,
        end_date: str,
        path: str,
        quiet: bool = False,
    ) -> None:
        if parameter in get_data.__IMDPARAMS:
            self.param = parameter
        else:
            raise ValueError(
                f"{parameter} is not available in IMD. {get_data.__IMDPARAMS}"
            )
        self.__imd = IMD(self.param)
        self.start_date, self.end_date = self.__imd._check_dates(start_date, end_date)
        self.download_path = self.__imd._checked_path(path)
        self.quiet = quiet
        self.total_days = (self.end_date - self.start_date).days + 1
        self.skipped_downloads = self.__download()
        if self.total_days == len(self.skipped_downloads):
            raise IOError(f'{self.param} data unavailable or inaccessible')

    def __download(self) -> List[str]:
        """When get_data initiated download of data from start date to end date
        will be carried out.

        Returns:
            List[str]: list of filenames for which download failed
        """
        date_range = self.__imd._dtrgen(self.start_date, self.end_date)
        output = []
        with ThreadPoolExecutor() as ex:
            futures = [
                ex.submit(self.__imd._download_grd, dt, self.download_path)
                for dt in date_range
            ]
        if self.quiet:
            for f in as_completed(futures):
                value = f.result()
                if value is not None:
                    output.append(value)
        else:
            with tqdm(total=self.total_days) as pbar:
                for f in as_completed(futures):
                    value = f.result()
                    if value is not None:
                        output.append(value)
                    pbar.update(1)
        return output

    def to_geotiff(self, path: str, single: bool = False) -> None:
        """conversion of downloaded grd data to geotiff format.

        Args:
            path (str): directory path to save the converted files
            single (bool): save as single tif file with daily data as bands
        """
        date_range = self.__imd._dtrgen(self.start_date, self.end_date)
        kwargs = {
            'total_days': self.total_days,
            'single': single,
            'download_path': self.download_path,
            'out_path': path,
            'date_range': date_range,
            'skipped_downloads': self.skipped_downloads,
            'x_list': self.skipped_downloads,
            'start_date': self.start_date,
            'end_date': self.end_date
        }
        if self.quiet:
            kwargs.update(pbar=None)
            self.__imd._to_geotiff_conversion(**kwargs)
        else:
            with tqdm(total=(self.total_days-len(self.skipped_downloads))) as pbar:
                kwargs.update(pbar=pbar)
                self.__imd._to_geotiff_conversion(**kwargs)

    def __len__(self) -> int:
        return self.total_days - len(self.skipped_downloads)

    @property
    def px_size(self) -> str:
        return f"{self.__imd._px_size} degree(s)"
