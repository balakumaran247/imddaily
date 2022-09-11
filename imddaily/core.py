import requests, os
from tqdm import tqdm
from datetime import datetime
from datetime import timedelta as td
from typing import Optional, Iterator, Tuple, Union
import numpy as np
import rasterio
from rasterio.crs import CRS
from affine import Affine


class IMD:

    __IMDURL = {
        "raingpm": "https://www.imdpune.gov.in/Seasons/Temperature/gpm/",
        "tmax": "https://www.imdpune.gov.in/Seasons/Temperature/max/",
        "tmin": "https://www.imdpune.gov.in/Seasons/Temperature/min/",
        "rain": "https://www.imdpune.gov.in/Seasons/Temperature/Rainfall/",
        "tmaxone": "https://www.imdpune.gov.in/Seasons/Temperature/max/",
        "tminone": "https://www.imdpune.gov.in/Seasons/Temperature/min/",
    }  # https://www.imdpune.gov.in/Seasons/Temperature/temp.html
    __IMDFMT = {
        "raingpm": ("", "%d%m%Y", "raingpm_"),
        "tmax": ("max", "%d%m%Y", "tmax_"),
        "tmin": ("min", "%d%m%Y", "tmin_"),
        "rain": ("rain_ind0.25_", "%y_%m_%d", "rain_"),
        "tmaxone": ("max1_", "%d%m%Y", "tmaxone_"),
        "tminone": ("min1_", "%d%m%Y", "tminone_"),
    }
    __ATTRS = {
        "raingpm": (281, 241, 0.25, -999.0, 'mm', 'Rainfall(GPM)'),
        "tmax": (61, 61, 0.5, 99.9, 'degree', 'Max Temperature'),
        "tmin": (61, 61, 0.5, 99.9, 'degree', 'Min Temperature'),
        "rain": (129, 135, 0.25, -999.0, 'mm', 'Rainfall'),
        "tmaxone": (31, 31, 1.0, 99.9, 'degree', 'Max Temperature'),
        "tminone": (31, 31, 1.0, 99.9, 'degree', 'Min Temperature'),
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
        self._lat_size, self._lon_size, self._px_size, self.__undef, self.__units, self.__name = IMD.__ATTRS[self.param]
        self._lat1, self._lat2, self._lon1, self._lon2 = IMD.__EXTENT[self.param]
        self.lat_array = np.linspace(self._lat1, self._lat2, self._lat_size)
        self.lon_array = np.linspace(self._lon1, self._lon2, self._lon_size)
        self.__transform = Affine(self._px_size, 0.0, (self._lon1-(self._px_size/2)), 0.0, -self._px_size, (self._lat2+(self._px_size/2)))
        self._profile = {
            'driver': 'GTiff',
            'dtype': 'float64',
            'nodata': self.__undef,
            'width': self._lon_size,
            'height': self._lat_size,
            'count': 1,
            'crs': CRS.from_epsg(4326),
            'transform': self.__transform,
            'tiled': False,
            'interleave': 'band'
        }

    def _download_grd(self, date: datetime, path: str, pbar: Optional[tqdm] = None) -> Optional[str]:
        url = f"{self.__imdurl}{self.__pfx}{date.strftime(self.__dtfmt)}.grd"
        filename, out_file = self._get_filepath(date, path, 'grd')
        if os.path.exists(out_file):
            if pbar: pbar.update(1)
            return filename
        r = requests.get(url, allow_redirects=True)
        if pbar: pbar.update(1)
        if r.status_code != 200:
            return filename
        with open(out_file, "wb") as f:
            f.write(r.content)
        return None

    def _get_filepath(self, date: datetime, path: str, ext: str) -> Tuple[str, str]:
        filename = f"{self.__opfx}{date.strftime('%Y%m%d')}.{ext}"
        return (filename, os.path.join(path, filename))

    def _check_path(self, path: str, type: int = 0, err_raise: bool = True) -> str:
        check_path = os.path.normpath(path)
        func = (os.path.isdir, os.path.isfile)[type]
        if not func(check_path):
            if err_raise: raise OSError(f"{check_path} does not exist.")
            return str()
        return check_path

    def _check_dates(self, start_date: str, end_date: str) -> Tuple[datetime, datetime]:
        self.__imd_first_date = {
            "raingpm": datetime.strptime('20151001', '%Y%m%d'),
            "tmax": datetime.strptime('20150601','%Y%m%d'),
            "tmin": datetime.strptime('20150601','%Y%m%d'),
            "rain": datetime.strptime('20181209', '%Y%m%d'),
            "tmaxone": datetime.strptime('20190101','%Y%m%d'),
            "tminone": datetime.strptime('20190101','%Y%m%d'),
        }
        self.__first_date = self.__imd_first_date[self.param]
        if not start_date:
            raise ValueError('Start Date is required.')
        end_date = (end_date, start_date)[end_date is None]
        sdate = datetime.strptime(start_date, "%Y-%m-%d")
        edate = datetime.strptime(end_date, "%Y-%m-%d")
        if sdate > edate:
            start_date, end_date = end_date, start_date
        if self.__first_date > sdate:
            raise ValueError(
                f'Data available after {self.__first_date.strftime("%Y-%m-%d")}')
        return (sdate, edate)

    def __read_grd(self, file_path: str) -> np.ndarray:
        with open(file_path, 'rb') as f:
            return np.fromfile(f, 'float32')#.reshape(self.__lat_size, self.__lon_size)

    def _transform_array(self, arr: np.ndarray, flip_ax: int) -> np.ndarray:
        arr = arr.reshape(self._lat_size, self._lon_size)
        return np.flip(arr, flip_ax)
        
    def _get_array(self, path: str, flip_ax: int) -> np.ndarray:
        return self._transform_array(self.__read_grd(path), flip_ax)

    # def _get_conc_array(self, date_range: Iterator[datetime], down_path: str) -> np.ndarray:
    #     conc = np.array([])
    #     for date in date_range:
    #         conc = np.append(conc, self._get_array(date, down_path))
        # return np.array(conc)

    def _dtrgen(self, start: datetime, end: datetime) -> Iterator[datetime]:
        return ((start+td(days=x)) for x in range((end-start).days+1))
