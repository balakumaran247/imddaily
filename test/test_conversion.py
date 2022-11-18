from imddaily import imddaily
import rasterio
import os, pytest
from datetime import datetime
from datetime import timedelta as td

prefix = {
    "raingpm": "raingpm_",
    "tmax": "tmax_",
    "tmin": "tmin_",
    "rain": "rain_",
    "tmaxone": "tmax1_",
    "tminone": "tmin1_",
}

shape_dict = {
    "raingpm": (281, 241),
    "tmax": (61, 61),
    "tmin": (61, 61),
    "rain": (129, 135),
    "tmaxone": (31, 31),
    "tminone": (31, 31),
}


def download_func(param, start_date, end_date, testpath, quiet):
    data = imddaily.get_data(param, start_date, end_date, testpath)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    dt_range = (start + td(days=x) for x in range((end - start).days + 1))
    return data, dt_range


@pytest.mark.parametrize(
    "param", ["raingpm", "tmax", "tmin", "rain", "tmaxone", "tminone"]
)
def test_conversion_files_exist_shape(param):
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    start_date, end_date = "2020-05-01", "2020-05-10"
    data, dt_range = download_func(param, start_date, end_date, testpath, False)
    data.to_geotiff(testpath)
    test_files_exits = [
        os.path.isfile(
            os.path.join(testpath, f"{prefix[param]}{dt.strftime('%Y%m%d')}.tif")
        )
        for dt in dt_range
    ]
    assert all(test_files_exits)
    for dt in dt_range:
        with rasterio.open(
            os.path.join(testpath, f"{prefix[param]}{dt.strftime('%Y%m%d')}.tif"), "r"
        ) as f:
            assert f.shape == shape_dict[param]


@pytest.mark.parametrize(
    "param", ["raingpm", "tmax", "tmin", "rain", "tmaxone", "tminone"]
)
def test_conversion_files_exist_shape_quiet(param):
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    start_date, end_date = "2020-05-11", "2020-05-20"
    data, dt_range = download_func(param, start_date, end_date, testpath, True)
    data.to_geotiff(testpath)
    test_files_exits = [
        os.path.isfile(
            os.path.join(testpath, f"{prefix[param]}{dt.strftime('%Y%m%d')}.tif")
        )
        for dt in dt_range
    ]
    assert all(test_files_exits)
    for dt in dt_range:
        with rasterio.open(
            os.path.join(testpath, f"{prefix[param]}{dt.strftime('%Y%m%d')}.tif"), "r"
        ) as f:
            assert f.shape == shape_dict[param]


def test_conversion_skipped():
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    data = imddaily.get_data("rain", "2020-06-21", "2020-06-30", testpath)
    data.to_geotiff(testpath)
    assert not os.path.isfile(os.path.join(testpath, "rain_20200624.tif"))


@pytest.mark.parametrize(
    "param", ["raingpm", "tmax", "tmin", "rain", "tmaxone", "tminone"]
)
def test_conversion_single(param):
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    start_date, end_date = "2020-04-01", "2020-04-10"
    data, dt_range = download_func(param, start_date, end_date, testpath, False)
    data.to_geotiff(testpath, True)
    out_path = os.path.join(testpath, f"{prefix[param]}20200401_20200410.tif")
    assert os.path.isfile(out_path)
    with rasterio.open(out_path, "r") as f:
        assert f.shape == shape_dict[param]
        assert f.count == 10
    data.to_geotiff(testpath)
    for idx, dt in enumerate(dt_range):
        with rasterio.open(
            os.path.join(testpath, f"{prefix[param]}{dt.strftime('%Y%m%d')}.tif"), "r"
        ) as ind:
            ind_arr = ind.read(1)
        with rasterio.open(out_path, "r") as sf:
            sf_arr = sf.read(idx + 1)
        assert (ind_arr == sf_arr).all()


@pytest.mark.parametrize(
    "param", ["raingpm", "tmax", "tmin", "rain", "tmaxone", "tminone"]
)
def test_conversion_single_quiet(param):
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    start_date, end_date = "2020-04-11", "2020-04-20"
    data, dt_range = download_func(param, start_date, end_date, testpath, True)
    data.to_geotiff(testpath, True)
    out_path = os.path.join(testpath, f"{prefix[param]}20200411_20200420.tif")
    assert os.path.isfile(out_path)
    with rasterio.open(out_path, "r") as f:
        assert f.shape == shape_dict[param]
        assert f.count == 10
    data.to_geotiff(testpath)
    for idx, dt in enumerate(dt_range):
        with rasterio.open(
            os.path.join(testpath, f"{prefix[param]}{dt.strftime('%Y%m%d')}.tif"), "r"
        ) as ind:
            ind_arr = ind.read(1)
        with rasterio.open(out_path, "r") as sf:
            sf_arr = sf.read(idx + 1)
        assert (ind_arr == sf_arr).all()
