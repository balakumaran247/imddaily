class IMDGPM:

    __URL = {
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
        self.__url = self.__URL[self.var_type]
        self.__prefix, self.__dtfmt = self.__IMDFILEFMT[self.var_type]

    def download_grd(self):
        pass

class MultiDateData(IMDGPM):
    """get the start date and end date as datetime and path
    loop through the dates and call download_grd
    and assign download_failed
    also check if file aready exist and assign skipped"""
    pass