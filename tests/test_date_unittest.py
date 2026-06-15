from datetime import datetime as dt
from dateutil.parser import ParserError
import pytest

from bento_transforms.tflib.date import convert_datetime, DatetimeFormats


def test_isoformat():
    new_dt = convert_datetime(
        "2012-01-19 17:21:00", tgt_format=DatetimeFormats.ISOFORMAT
    )
    assert new_dt == "2012-01-19T17:21:00"


def test_non_routine_converts():
    """The expectation is that all 'format_str' enums are just shortcuts
    to format strings that can be used with strftime, so we can check
    that that is still true"""
    for entry in DatetimeFormats:
        if "format_str" in entry.value:
            now1 = dt.now()
            expected_format = now1.strftime(entry.value["format_str"])
            new_dt = convert_datetime(str(now1), tgt_format=entry)
            assert new_dt == expected_format


def test_wrong_tgt_format():
    with pytest.raises(AttributeError, match="object has no attribute"):
        new_dt = convert_datetime("2012-01-19 17:21:00", tgt_format=6)


def test_wrong_tgt_format_enum():
    with pytest.raises(AttributeError, match="has no attribute"):
        new_dt = convert_datetime(
            "2012-01-19 17:21:00", tgt_format=DatetimeFormats.WRONG
        )


def test_date_string_fail_unknown():
    with pytest.raises(ParserError, match="Unknown string format"):
        new_dt = convert_datetime("stephen", tgt_format=DatetimeFormats.ISOFORMAT)


def test_date_string_fail_month():
    with pytest.raises(ParserError, match="month must be in"):
        new_dt = convert_datetime(
            "2012-13-19 17:21:00", tgt_format=DatetimeFormats.ISOFORMAT
        )


def test_date_string_fail_day():
    with pytest.raises(ParserError, match="day is out of range for month"):
        new_dt = convert_datetime(
            "2012-01-40 17:21:00", tgt_format=DatetimeFormats.ISOFORMAT
        )


def test_date_string_fail_year():
    year = 19000
    with pytest.raises(ParserError, match=f"year {year} is out of range"):
        new_dt = convert_datetime(
            f"{year}-01-19 17:21:00", tgt_format=DatetimeFormats.ISOFORMAT
        )
