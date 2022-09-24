from imddaily import imddaily
import os, pytest
from datetime import datetime
from datetime import timedelta as td


def test_dates_start_None():
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    with pytest.raises(ValueError, match="Start Date is required."):
        imddaily.get_data("rain", None, "2020-06-10", testpath)


def test_dates_unavailable():
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    with pytest.raises(ValueError, match="Data available after 2018-12-09"):
        imddaily.get_data("rain", "2015-01-01", "2015-01-10", testpath)


def test_dates_end_None():
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    data_none = imddaily.get_data("rain", "2020-06-01", None, testpath)
    assert data_none.start_date.strftime("%Y-%m-%d") == "2020-06-01"
    assert data_none.end_date.strftime("%Y-%m-%d") == "2020-06-01"


def test_dates_same():
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    data_same = imddaily.get_data("rain", "2020-06-01", "2020-06-01", testpath)
    assert data_same.start_date.strftime("%Y-%m-%d") == "2020-06-01"
    assert data_same.end_date.strftime("%Y-%m-%d") == "2020-06-01"


def test_dates_reverse():
    testpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_data")
    data_reverse = imddaily.get_data("rain", "2020-06-10", "2020-06-01", testpath)
    assert data_reverse.start_date.strftime("%Y-%m-%d") == "2020-06-01"
    assert data_reverse.end_date.strftime("%Y-%m-%d") == "2020-06-10"
