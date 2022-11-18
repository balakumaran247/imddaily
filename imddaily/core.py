"""Core of the imddaily package which contains all the class and methods to
download and convert the IMD data.

Raises:
    OSError: directory path does not exist
    ValueError: Start Date is mandatory
    ValueError: Provided date format cannot be recognized
"""
import requests, os
from datetime import datetime
from datetime import timedelta as td
from typing import Optional, Iterator, Tuple
import numpy as np
import rasterio
from rasterio.crs import CRS
from affine import Affine
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed


class IMD:
    """Main class of the imddaily pacakage which contains all the variable and
    methods to download and convert IMD real time data.

    Args:
        param (str): one of 'raingpm','tmax','tmin','rain','tmaxone','tminone'

    Raises:
        OSError: directory path does not exist
        ValueError: Start Date is mandatory
        ValueError: Provided date format cannot be recognized
    """

    __IMDURL = {
        "raingpm": "https://www.imdpune.gov.in/cmpg/Realtimedata/gpm/",
        "tmax": "https://www.imdpune.gov.in/cmpg/Realtimedata/max/",
        "tmin": "https://www.imdpune.gov.in/cmpg/Realtimedata/min/",
        "rain": "https://www.imdpune.gov.in/cmpg/Realtimedata/Rainfall/",
        "tmaxone": "https://www.imdpune.gov.in/cmpg/Realtimedata/maxone/",
        "tminone": "https://www.imdpune.gov.in/cmpg/Realtimedata/minone/",
    }  # https://www.imdpune.gov.in/lrfindex.php
    __IMDFMT = {
        "raingpm": ("", "%d%m%Y", "raingpm_"),
        "tmax": ("max", "%d%m%Y", "tmax_"),
        "tmin": ("min", "%d%m%Y", "tmin_"),
        "rain": ("rain_ind0.25_", "%y_%m_%d", "rain_"),
        "tmaxone": ("max1_", "%d%m%Y", "tmax1_"),
        "tminone": ("min1_", "%d%m%Y", "tmin1_"),
    }
    __ATTRS = {
        "raingpm": (281, 241, 0.25, -999.0, "mm", "Rainfall(GPM)"),
        "tmax": (61, 61, 0.5, 99.9, "degree C", "Max Temperature"),
        "tmin": (61, 61, 0.5, 99.9, "degree C", "Min Temperature"),
        "rain": (129, 135, 0.25, -999.0, "mm", "Rainfall"),
        "tmaxone": (31, 31, 1.0, 99.9, "degree C", "Max Temperature"),
        "tminone": (31, 31, 1.0, 99.9, "degree C", "Min Temperature"),
    }
    __EXTENT = {
        "raingpm": (-30.0, 40.0, 50.0, 110.0),
        "tmax": (7.5, 37.5, 67.5, 97.5),
        "tmin": (7.5, 37.5, 67.5, 97.5),
        "rain": (6.5, 38.5, 66.5, 100.0),
        "tmaxone": (7.5, 37.5, 67.5, 97.5),
        "tminone": (7.5, 37.5, 67.5, 97.5),
    }

    def __init__(self, param: str) -> None:
        self.param = param
        self.__imdurl = IMD.__IMDURL[self.param]
        self.__pfx, self.__dtfmt, self.__opfx = IMD.__IMDFMT[self.param]
        (
            self._lat_size,
            self._lon_size,
            self._px_size,
            self.__undef,
            self.__units,
            self.__name,
        ) = IMD.__ATTRS[self.param]
        self._lat1, self._lat2, self._lon1, self._lon2 = IMD.__EXTENT[self.param]
        self._lat_array = np.linspace(self._lat1, self._lat2, self._lat_size)
        self._lon_array = np.linspace(self._lon1, self._lon2, self._lon_size)
        self.__transform = Affine(
            self._px_size,
            0.0,
            (self._lon1 - (self._px_size / 2)),
            0.0,
            -self._px_size,
            (self._lat2 + (self._px_size / 2)),
        )
        self._profile = {
            "driver": "GTiff",
            "dtype": "float64",
            "nodata": self.__undef,
            "width": self._lon_size,
            "height": self._lat_size,
            "count": 1,
            "crs": CRS.from_epsg(4326),
            "transform": self.__transform,
            "tiled": False,
            "interleave": "band",
        }

    def fetch_grd(self, url: str) -> Tuple[bool, requests.Response]:
        """download of grd data from the url provided

        Args:
            url (str): url to download the grd data

        Returns:
            Tuple[bool, requests.Response]: status and response of the requests call
        """
        r = requests.get(url, allow_redirects=True)
        return (r.status_code == 200, r)

    def _download_grd(self, date: datetime, path: str) -> Optional[str]:
        """download of grd data for given date and stored in given file path

        Args:
            date (datetime): date for download of data
            path (str): file path where downloaded data will be stored in .grd

        Returns:
            Optional[str]: date if download failed or None if succeed
        """
        url = f"{self.__imdurl}{self.__pfx}{date.strftime(self.__dtfmt)}.grd"
        _, out_file = self._get_filepath(date, path, "grd")
        status, r = self.fetch_grd(url)
        if not status:
            return date.strftime("%Y-%m-%d")
        with open(out_file, "wb") as f:
            f.write(r.content)
        return None

    def _get_filepath(self, date: datetime, path: str, ext: str, xdate: Optional[datetime] = None) -> Tuple[str, str]:
        """generate file path for provided date and format in the provided
        directory path

        Args:
            date (datetime): date for which the file path to be created
            path (str): directory path
            ext (str): file extension
            xdate (Optional[datetime]): second date if needed in filename, defaults to None.

        Returns:
            Tuple[str, str]: file name and the file path
        """
        extra = f'_{xdate:%Y%m%d}' if xdate else ''
        filename = f"{self.__opfx}{date:%Y%m%d}{extra}.{ext}"
        return (filename, os.path.join(path, filename))

    def _checked_path(self, path: str, type: int = 0, err_raise: bool = True) -> str:
        """Check the existance of directory or file path based on mentioned type

        Args:
            path (str): file path
            type (int, optional): 0 is directory or 1 is file. Defaults to 0.
            err_raise (bool, optional): raise error if path does not exist. Defaults to True.

        Raises:
            OSError: path does not exist

        Returns:
            str: path in str type if exist or empty string
        """
        check_path = os.path.normpath(path)
        func = (os.path.isdir, os.path.isfile)[type]
        if not func(check_path):
            if err_raise:
                raise OSError(f"{check_path} does not exist.")
            return str()
        return check_path

    def _check_dates(self, start_date: str, end_date: str) -> Tuple[datetime, datetime]:
        """check the provided dates for several conditions

        Args:
            start_date (str): start date in the format YYYY-MM-DD
            end_date (str): end date in the format YYYY-MM-DD

        Raises:
            ValueError: Start Date is mandatory
            ValueError: Data not available for provided date range

        Returns:
            Tuple[datetime, datetime]: start date and end date
        """
        self.__imd_first_date = {
            "raingpm": datetime.strptime("20151001", "%Y%m%d"),
            "tmax": datetime.strptime("20150601", "%Y%m%d"),
            "tmin": datetime.strptime("20150601", "%Y%m%d"),
            "rain": datetime.strptime("20181209", "%Y%m%d"),
            "tmaxone": datetime.strptime("20190101", "%Y%m%d"),
            "tminone": datetime.strptime("20190101", "%Y%m%d"),
        }
        self.__first_date = self.__imd_first_date[self.param]
        if not start_date:
            raise ValueError("Start Date is required.")
        end_date = (end_date, start_date)[end_date is None]
        sdate = datetime.strptime(start_date, "%Y-%m-%d")
        edate = datetime.strptime(end_date, "%Y-%m-%d")
        if sdate > edate:
            sdate, edate = edate, sdate
        if self.__first_date > sdate:
            raise ValueError(
                f'Data available after {self.__first_date.strftime("%Y-%m-%d")}'
            )
        return (sdate, edate)

    def __read_grd(self, file_path: str) -> np.ndarray:
        """read the input grd file as numpy ndarray

        Args:
            file_path (str): path for the grd file

        Returns:
            np.ndarray: grd file read as numpy ndarray
        """
        with open(file_path, "rb") as f:
            return np.fromfile(f, "float32")

    def _transform_array(self, arr: np.ndarray, flip_ax: int, num_bands: Optional[int] = None) -> np.ndarray:
        """reshape and flip the numpy ndarray

        Args:
            arr (np.ndarray): grd data read as numpy ndarray
            flip_ax (int): axis along which to flip the array
            num_bands (Optional[int]): number of bands in a single tif file

        Returns:
            np.ndarray: transformed array
        """
        if num_bands:
            arr = arr.reshape(num_bands, self._lat_size, self._lon_size)
        else:
            arr = arr.reshape(self._lat_size, self._lon_size)
        return np.flip(arr, flip_ax)

    def _to_numpy(self, path: str, flip_ax: int) -> np.ndarray:
        """read the grd array as numpy array and transform the array

        Args:
            path (str): path of the grd file
            flip_ax (int): axis along which to flip the array

        Returns:
            np.ndarray: correct grd data as numpy ndarray
        """
        return self._transform_array(self.__read_grd(path), flip_ax)

    def _get_array(
        self, date: datetime, grd_dir: str, tif_dir: str
    ) -> Tuple[datetime, str, np.ndarray]:
        """read and transform grd file if it exist or return numpy array with
        no data values

        Args:
            date (datetime): date of the data being read
            grd_dir (str): path to grd file
            tif_dir (str): path for the tif file

        Returns:
            Tuple[datetime, str, np.ndarray]: date, tif file path and numpy array
        """
        _, filepath = self._get_filepath(date, grd_dir, "grd")
        if self._checked_path(filepath, 1, err_raise=False):
            data = self._to_numpy(filepath, 0)
        else:
            data = np.full((self._lat_size, self._lon_size), self.__undef)
        _, out_file = self._get_filepath(date, tif_dir, "tif")
        return (date, out_file, data)

    def _dtrgen(self, start: datetime, end: datetime) -> Iterator[datetime]:
        """date range generator object from start date to end date

        Args:
            start (datetime): start date
            end (datetime): end date

        Yields:
            Iterator[datetime]: generator object of datetime ranging from start date to end date
        """
        return ((start + td(days=x)) for x in range((end - start).days + 1))
    
    def __get_futures(self, **kwargs):
        with ProcessPoolExecutor() as ex:
            return [
                ex.submit(self._get_array, date, kwargs['download_path'], kwargs['out_path'])
                for date in kwargs['date_range']
                if f'{date:%Y-%m-%d}' not in kwargs['x_list']
            ]

    def _to_geotiff_conversion(self, **kwargs):
        # total_days, single, pbar, download_path, out_path, date_range, x_list
        # start_date, end_date, skipped_downloads
        if kwargs['single']:
            kwargs.update(x_list=list())
            self.__single_tif_conv(**kwargs)
        else:
            self.__tif_conv(**kwargs)

    def __single_tif_conv(self, **kwargs):
        futures = self.__get_futures(**kwargs)
        _, out_file = self._get_filepath(kwargs['start_date'],kwargs['out_path'],'tif',kwargs['end_date'])
        self._profile.update(count=kwargs['total_days'])
        single_arr = np.array([])
        for f in futures:
            _, _, data = f.result()
            single_arr = np.append(single_arr, data)
        single_arr = self._transform_array(single_arr, 0, kwargs['total_days'])
        with rasterio.open(out_file, "w", **self._profile) as dst:
            dst.write(single_arr[::-1])
        if kwargs['pbar']: kwargs['pbar'].update(kwargs['total_days']-len(kwargs['skipped_downloads']))

    def __tif_conv(self, **kwargs):
        futures = self.__get_futures(**kwargs)
        self._profile.update(count=1)
        for f in as_completed(futures):
            _, out_file, data = f.result()
            with rasterio.open(out_file, "w", **self._profile) as dst:
                dst.write(data, 1)
            if kwargs['pbar']: kwargs['pbar'].update(1)