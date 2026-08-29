"""The 4 AM business-day boundary. Get this wrong and every late-night sale
lands on the wrong day, which corrupts every weekday baseline in the system."""

from datetime import date, datetime

import pytest

from thbev.timeutil import (
    business_day_bounds,
    business_day_of,
    business_days_between,
    hour_slot,
)


@pytest.mark.parametrize(
    "stamp, expected",
    [
        (datetime(2026, 8, 31, 1, 30), date(2026, 8, 30)),   # 01:30 -> prior day
        (datetime(2026, 8, 31, 3, 59), date(2026, 8, 30)),   # last minute before rollover
        (datetime(2026, 8, 31, 4, 0), date(2026, 8, 31)),    # rollover
        (datetime(2026, 8, 31, 4, 1), date(2026, 8, 31)),
        (datetime(2026, 8, 30, 23, 59), date(2026, 8, 30)),
        (datetime(2026, 8, 30, 0, 0), date(2026, 8, 29)),    # midnight belongs to prior day
    ],
)
def test_business_day_boundary(stamp, expected):
    assert business_day_of(stamp) == expected


def test_business_day_is_configurable():
    stamp = datetime(2026, 8, 31, 2, 0)
    assert business_day_of(stamp, cutoff_hour=0) == date(2026, 8, 31)
    assert business_day_of(stamp, cutoff_hour=4) == date(2026, 8, 30)


def test_business_day_rejects_bad_cutoff():
    with pytest.raises(ValueError):
        business_day_of(datetime(2026, 8, 31, 2, 0), cutoff_hour=25)


def test_business_day_bounds_span_the_night():
    start, end = business_day_bounds(date(2026, 8, 30))
    assert start == datetime(2026, 8, 30, 4, 0)
    assert end == datetime(2026, 8, 31, 4, 0)


def test_hour_slot_is_relative_to_the_cutoff():
    assert hour_slot(datetime(2026, 8, 30, 4, 30)) == 0
    assert hour_slot(datetime(2026, 8, 30, 17, 0)) == 13
    assert hour_slot(datetime(2026, 8, 31, 3, 30)) == 23


def test_business_days_between_is_inclusive():
    days = business_days_between(date(2026, 8, 24), date(2026, 8, 30))
    assert len(days) == 7
    assert days[0].weekday() == 0 and days[-1].weekday() == 6
    with pytest.raises(ValueError):
        business_days_between(date(2026, 8, 30), date(2026, 8, 24))
