import requests, os
from tqdm import tqdm
from datetime import datetime
from datetime import timedelta as td
from typing import Optional, Iterator, Tuple, Union
import numpy as np
import xarray as xr


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
        self.__lat_size, self.__lon_size, self._grid_size, self.__undef, self.__units, self.__name = IMD.__ATTRS[self.param]
        self.lat1, self.lat2, self.lon1, self.lon2 = IMD.__EXTENT[self.param]
        self.lat_array = np.linspace(self.lat1, self.lat2, self.__lat_size)
        self.lon_array = np.linspace(self.lon1, self.lon2, self.__lon_size)

    def _download_grd(self, date: datetime, path: str, pbar: Optional[tqdm] = None) -> Optional[str]:
        url = f"{self.__imdurl}{self.__pfx}{date.strftime(self.__dtfmt)}.grd"
        filename, out_file = self.__get_filepath(date, path, 'grd')
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

    def __get_filepath(self, date: datetime, path: str, ext: str) -> Tuple[str, str]:
        filename = f"{self.__opfx}{date.strftime('%Y%m%d')}.{ext}"
        return (filename, os.path.join(path, filename))

    def _check_path(self, path: str) -> str:
        check_path = os.path.normpath(path)
        if not os.path.isdir(check_path):
            raise OSError(f"{check_path} does not exist.")
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

    def _reshape_array(self, time: int, arr: np.ndarray) -> np.ndarray:
        arr = arr.reshape(time, self.__lon_size, self.__lat_size)
        return np.swapaxes(arr, 1, 2)
        
    def _get_array(self, date: datetime, down_path: str) -> np.ndarray:
        _, filepath = self.__get_filepath(date, down_path, 'grd')
        return self.__read_grd(filepath)

    def _get_conc_array(self, date_range: Iterator[datetime], down_path: str) -> np.ndarray:
        conc = np.array([])
        for date in date_range:
            conc = np.append(conc, self._get_array(date, down_path))
        return np.array(conc)

    def _get_xarray(self, time: Iterator[datetime], arr: np.ndarray):
        xr_da = xr.Dataset({self.param: (['time', 'lat', 'lon'], arr,
                                     {'units': self.__units, 'long_name': self.__name})},
                           coords={'lat': self.lat_array,
                                   'lon': self.lon_array, 'time': time})
        xr_da_masked = xr_da.where(xr_da.values != self.__undef)
        
        xr_da_masked.time.encoding['units'] = 'days'
        xr_da_masked.time.attrs['standard_name'] = 'time'
        xr_da_masked.time.attrs['long_name'] = 'time'

        xr_da_masked.lon.attrs['axis'] = 'X'
        xr_da_masked.lon.attrs['long_name'] = 'longitude'
        xr_da_masked.lon.attrs['long_name'] = 'longitude'
        xr_da_masked.lon.attrs['units'] = 'degrees_east'

        xr_da_masked.lat.attrs['axis'] = 'Y'
        xr_da_masked.lat.attrs['standard_name'] = 'latitude'
        xr_da_masked.lat.attrs['long_name'] = 'latitude'
        xr_da_masked.lat.attrs['units'] = 'degrees_north'
        
        xr_da_masked.attrs['Conventions'] = 'CF-1.7'
        xr_da_masked.attrs['title'] = 'IMD gridded data'
        xr_da_masked.attrs['source'] = 'https://imdpune.gov.in/'
        xr_da_masked.attrs['history'] = str(datetime.utcnow()) + ' Python'
        xr_da_masked.attrs['references'] = ''
        xr_da_masked.attrs['comment'] = ''
        xr_da_masked.attrs['crs'] = 'epsg:4326'
        
        return xr_da_masked
    
    def _dtrgen(self, start: datetime, end: datetime) -> Iterator[datetime]:
        return ((start+td(days=x)) for x in range((end-start).days+1))
