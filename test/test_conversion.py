from imddaily import imddaily
import rasterio
import os, pytest
from datetime import datetime
from datetime import timedelta as td


@pytest.mark.parametrize(
    "param", ["raingpm", "tmax", "tmin", "rain", "tmaxone", "tminone"]
)
def test_conversion_files_exist(param):
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
    data.to_geotiff(testpath)
    start = datetime.strptime("2020-06-01", "%Y-%m-%d")
    end = datetime.strptime("2020-06-10", "%Y-%m-%d")
    dt_range = (start + td(days=x) for x in range((end - start).days + 1))
    test_files_exits = [
        os.path.isfile(
            os.path.join(testpath, f"{prefix[param]}{dt.strftime('%Y%m%d')}.tif")
        )
        for dt in dt_range
    ]
    assert all(test_files_exits)


def test_conversion_skipped():
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    data = imddaily.get_data("rain", "2020-06-21", "2020-06-30", testpath)
    data.to_geotiff(testpath)
    assert not os.path.isfile(os.path.join(testpath, "rain_20200624.tif"))


@pytest.mark.parametrize(
    "param", ["raingpm", "tmax", "tmin", "rain", "tmaxone", "tminone"]
)
def test_conversion_shape(param):
    shape_dict = {
        "raingpm": (281, 241),
        "tmax": (61, 61),
        "tmin": (61, 61),
        "rain": (129, 135),
        "tmaxone": (31, 31),
        "tminone": (31, 31),
    }
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
    data.to_geotiff(testpath)
    start = datetime.strptime("2020-06-01", "%Y-%m-%d")
    end = datetime.strptime("2020-06-10", "%Y-%m-%d")
    dt_range = (start + td(days=x) for x in range((end - start).days + 1))
    for dt in dt_range:
        with rasterio.open(
            os.path.join(testpath, f"{prefix[param]}{dt.strftime('%Y%m%d')}.tif"), "r"
        ) as f:
            assert f.shape == shape_dict[param]
