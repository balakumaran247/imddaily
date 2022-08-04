import requests, os
from datetime import datetime
from typing import Optional


class IMD:

    __IMDURL = {
        "rain": "https://www.imdpune.gov.in/Seasons/Temperature/gpm/",
        "tmax": "https://www.imdpune.gov.in/Seasons/Temperature/max/",
        "tmin": "https://www.imdpune.gov.in/Seasons/Temperature/min/",
        "raingrd": "https://www.imdpune.gov.in/Seasons/Temperature/Rainfall/",
        "tmaxone": "https://www.imdpune.gov.in/Seasons/Temperature/max/",
        "tminone": "https://www.imdpune.gov.in/Seasons/Temperature/min/",
    }  # https://www.imdpune.gov.in/Seasons/Temperature/temp.html
    __IMDFILEFMT = {
        "rain": ("", "%d%m%Y"),
        "tmax": ("max", "%d%m%Y"),
        "tmin": ("min", "%d%m%Y"),
        "raingrd": ("rain_ind0.25_", "%y_%m_%d"),
        "tmaxone": ("max1_", "%d%m%Y"),
        "tminone": ("min1_", "%d%m%Y"),
    }

    def __init__(self, var_type: str) -> None:
        self.var_type = var_type
        self.__imdurl = IMD.__IMDURL[self.var_type]
        self.__pfx, self.__dtfmt = IMD.__IMDFILEFMT[self.var_type]

    def download_grd(self, dt: datetime, path: str) -> Optional[str]:
        url = f"{self.__imdurl}{self.__pfx}{dt.strftime(self.__dtfmt)}.grd"
        filename = f"{dt.strftime('%Y%m%d')}.grd"
        out_file = os.path.join(path, filename)
        r = requests.get(url, allow_redirects=True)
        if os.path.exists(out_file) or r.status_code != 200:
            return filename
        with open(out_file, "wb") as f:
            f.write(r.content)
        return None


# class MultiDateData(IMD):
#     """get the start date and end date as datetime and path
#     loop through the dates and call download_grd
#     and assign download_failed
#     also check if file aready exist and assign skipped"""
#     pass
