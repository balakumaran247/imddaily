from imddaily import imddaily
import os, pytest
from datetime import datetime
from datetime import timedelta as td

testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
prefix = {
    "raingpm": "raingpm_",
    "tmax": "tmax_",
    "tmin": "tmin_",
    "rain": "rain_",
    "tmaxone": "tmax1_",
    "tminone": "tmin1_",
}
param_list = ["raingpm", "tmax", "tmin", "rain", "tmaxone", "tminone"]


def download_func(param, start_date, end_date, quiet):
    data = imddaily.get_data(param, start_date, end_date, testpath, quiet)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    dt_range = (start + td(days=x) for x in range((end - start).days + 1))
    return data, dt_range


@pytest.mark.parametrize("param", param_list)
def test_download_files_exist(param):
    start_date, end_date = "2020-07-01", "2020-07-10"
    data, dt_range = download_func(param, start_date, end_date, False)
    test_files_exits = [
        os.path.isfile(
            os.path.join(testpath, f"{prefix[param]}{dt.strftime('%Y%m%d')}.grd")
        )
        for dt in dt_range
    ]
    assert all(test_files_exits)
    assert data.total_days == 10
    assert data.skipped_downloads == []


@pytest.mark.parametrize("param", param_list)
def test_download_files_exist_quiet(param):
    start_date, end_date = "2020-07-11", "2020-07-20"
    data, dt_range = download_func(param, start_date, end_date, True)
    test_files_exits = [
        os.path.isfile(
            os.path.join(testpath, f"{prefix[param]}{dt.strftime('%Y%m%d')}.grd")
        )
        for dt in dt_range
    ]
    assert all(test_files_exits)
    assert data.total_days == 10
    assert data.skipped_downloads == []


def test_download_skipped():
    data, _ = download_func("rain", "2020-06-21", "2020-06-30", False)
    assert not os.path.isfile(os.path.join(testpath, "rain_20200624.grd"))
    assert len(data.skipped_downloads) == 1
    assert "2020-06-24" in data.skipped_downloads
