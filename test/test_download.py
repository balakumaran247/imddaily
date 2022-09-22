from imddaily import imddaily
import os, pytest
from datetime import datetime
from datetime import timedelta as td

@pytest.mark.parametrize(
    "param", ["raingpm", "tmax", "tmin", "rain", "tmaxone", "tminone"]
)
def test_download_files_exist(param):
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    prefix = {
        "raingpm": "raingpm_",
        "tmax": "tmax_",
        "tmin": "tmin_",
        "rain": "rain_",
        "tmaxone": "tmax1_",
        "tminone": "tmin1_",
    }
    data = imddaily.get_data(param, "2020-06-01", "2020-06-10", testpath)
    start = datetime.strptime("2020-06-01", "%Y-%m-%d")
    end = datetime.strptime("2020-06-10", "%Y-%m-%d")
    dt_range = (start + td(days=x) for x in range((end - start).days + 1))
    test_files_exits = [
        os.path.isfile(
            os.path.join(testpath, f"{prefix[param]}{dt.strftime('%Y%m%d')}.grd")
        )
        for dt in dt_range
    ]

    assert all(test_files_exits)
