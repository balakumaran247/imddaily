from datetime import datetime
from typing import List
from .core import IMD
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import rasterio


class get_data:
    __IMDPARAMS = ('raingpm','tmax','tmin','rain','tmaxone','tminone')
    def __init__(self, parameter: str, start_date: str, end_date: str, path: str, use_async: bool = True, quiet: bool = True) -> None:
        if parameter in get_data.__IMDPARAMS:
            self.param = parameter
        else:
            raise ValueError(f'{parameter} is not available in IMD. {get_data.__IMDPARAMS}')
        self.__imd = IMD(self.param)
        self.start_date, self.end_date = self.__imd._check_dates(start_date, end_date)
        self.download_path = self.__imd._check_path(path)
        self.use_async = use_async
        self.quiet = quiet
        self.total_days = (self.end_date-self.start_date).days+1
        self.skipped_downloads = self.__download()
        self.failed_conversions = []

    def __download(self) -> List:
        date_range = self.__imd._dtrgen(self.start_date, self.end_date)
        if self.use_async:
            if self.quiet:
                with ThreadPoolExecutor() as ex:
                    futures = [ex.submit(self.__imd._download_grd, dt, self.download_path) for dt in date_range]
            else:
                with tqdm(total=self.total_days) as pbar:
                    with ThreadPoolExecutor() as ex:
                        futures = [ex.submit(self.__imd._download_grd, dt, self.download_path, pbar) for dt in date_range]
            downloads = [future.result() for future in futures if future is not None]
        else:
            if self.quiet:
                downloads = [self.__imd._download_grd(dt, self.download_path) for dt in date_range]
            else:
                with tqdm(total=self.total_days) as pbar:
                    downloads = [self.__imd._download_grd(dt, self.download_path, pbar) for dt in date_range]
        return list(filter(lambda x : x, downloads))

    def to_tif(self, path: str):
        date_range = self.__imd._dtrgen(self.start_date, self.end_date)
        for date in date_range:
            _, filepath = self.__imd._get_filepath(date, self.download_path, 'grd')
            if self.__imd._check_path(filepath, 1, err_raise=False):
                data = self.__imd._get_array(filepath, 0)
                _, out_file = self.__imd._get_filepath(date, path, 'tif')
                with rasterio.open(out_file, 'w', **self.__imd._profile) as dst:
                    dst.write(data, 1)

    # def to_single_tif(self, path: str):
    #     date_range = self.__imd._dtrgen(self.start_date, self.end_date)
    #     data = self.__imd._get_conc_array(date_range, self.download_path)
    #     print(type(data))
    #     print(data.shape)

    def __len__(self) -> int:
        return self.total_days - len(self.skipped_downloads)

    @property
    def px_size(self) -> float:
        return self.__imd._px_size