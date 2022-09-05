import imddaily
import os
from datetime import datetime
from datetime import timedelta as td


def test_download_files_exist():
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    data = imddaily.get_data("rain", "2020-06-01", "2020-06-10", testpath)
    start = datetime.strptime("2020-06-01", "%Y-%m-%d")
    end = datetime.strptime("2020-06-10", "%Y-%m-%d")
    dt_range = (start + td(days=x) for x in range((end - start).days + 1))
    test_files_exits = [
        os.path.isfile(os.path.join(testpath, f"rain_{dt.strftime('%Y%m%d')}.grd"))
        for dt in dt_range
    ]

    assert all(test_files_exits)
