"""Main file of the imddaily package while organizes all the functionalities like
download and convert the real time data from IMD.
"""
from typing import List
from .core import IMD
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import rasterio

__version__ = "0.2.1"


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

    def __download(self) -> List[str]:
        """When get_data initiated download of data from start date to end date
        will be carried out.

        Returns:
            List[str]: list of filenames for which download failed
        """
        date_range = self.__imd._dtrgen(self.start_date, self.end_date)
        output = []
        if self.quiet:
            with ThreadPoolExecutor() as ex:
                futures = [
                    ex.submit(self.__imd._download_grd, dt, self.download_path)
                    for dt in date_range
                ]
                for f in as_completed(futures):
                    value = f.result()
                    if value is not None:
                        output.append(value)
        else:
            with tqdm(total=self.total_days) as pbar:
                with ThreadPoolExecutor() as ex:
                    futures = [
                        ex.submit(self.__imd._download_grd, dt, self.download_path)
                        for dt in date_range
                    ]
                    for f in as_completed(futures):
                        value = f.result()
                        if value is not None:
                            output.append(value)
                        pbar.update(1)
        return output

    def to_geotiff(self, path: str) -> None:
        """conversion of downloaded grd data to geotiff format.

        Args:
            path (str): directory path to save the converted files
        """
        date_range = self.__imd._dtrgen(self.start_date, self.end_date)
        if self.quiet:
            with ProcessPoolExecutor() as ex:
                futures = [
                    ex.submit(self.__imd._get_array, date, self.download_path, path)
                    for date in date_range
                    if date.strftime("%Y-%m-%d") not in self.skipped_downloads
                ]
                for f in as_completed(futures):
                    _, out_file, data = f.result()
                    with rasterio.open(out_file, "w", **self.__imd._profile) as dst:
                        dst.write(data, 1)
        else:
            with tqdm(total=(self.total_days-len(self.skipped_downloads))) as pbar:
                with ProcessPoolExecutor() as ex:
                    futures = [
                        ex.submit(self.__imd._get_array, date, self.download_path, path)
                        for date in date_range
                        if date.strftime("%Y-%m-%d") not in self.skipped_downloads
                    ]
                    for f in as_completed(futures):
                        _, out_file, data = f.result()
                        with rasterio.open(out_file, "w", **self.__imd._profile) as dst:
                            dst.write(data, 1)
                        pbar.update(1)

    def __len__(self) -> int:
        return self.total_days - len(self.skipped_downloads)

    @property
    def px_size(self) -> str:
        return f"{self.__imd._px_size} degree(s)"
