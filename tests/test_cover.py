"""Days of cover, per vendor. Never a flat seven."""

from __future__ import annotations

from datetime import datetime

import pytest

from thbev.ordering import NoOrderWindow, plan_delivery, upcoming_cutoffs

SUNDAY_AFTERNOON = datetime(2026, 8, 30, 16, 0)


def test_superior_sunday_only_covers_a_full_week(catalog):
    plan = plan_delivery(catalog, "superior", SUNDAY_AFTERNOON)
    assert plan.window.key == "superior_sunday"
    assert plan.delivery == datetime(2026, 8, 31, 9, 0)     # Monday
    assert plan.next_delivery == datetime(2026, 9, 7, 9, 0)  # next Monday
    assert plan.days_of_cover == 7


def test_superior_with_the_thursday_window_only_covers_four_days(catalog):
    """Monday to Friday is four days, not seven. This halves the order."""
    plan = plan_delivery(catalog, "superior", SUNDAY_AFTERNOON, include_optional=True)
    assert plan.next_delivery == datetime(2026, 9, 4, 9, 0)  # Friday
    assert plan.days_of_cover == 4


def test_southern_glazers_tuesday_drop_covers_eight_days(catalog):
    """Tuesday to Tuesday is seven days plus the vendor's configured buffer."""
    plan = plan_delivery(catalog, "southern_glazers", SUNDAY_AFTERNOON)
    assert plan.window.key == "sgws_monday"
    assert plan.delivery == datetime(2026, 9, 1, 9, 0)   # Tuesday
    assert plan.gap_days == 7
    assert plan.buffer_days == 1
    assert plan.days_of_cover == 8


def test_southern_glazers_with_the_followup_covers_less(catalog):
    plan = plan_delivery(catalog, "southern_glazers", SUNDAY_AFTERNOON, include_optional=True)
    assert plan.next_delivery == datetime(2026, 9, 4, 9, 0)  # Friday
    assert plan.days_of_cover == 4  # 3-day gap plus the 1-day buffer


def test_arena_and_heidelberg_have_their_own_calendars(catalog):
    arena = plan_delivery(catalog, "arena", SUNDAY_AFTERNOON)
    assert arena.cutoff == datetime(2026, 8, 30, 17, 0)
    assert arena.days_of_cover == 7
    arena_both = plan_delivery(catalog, "arena", SUNDAY_AFTERNOON, include_optional=True)
    assert arena_both.next_delivery == datetime(2026, 9, 3, 17, 0)  # Thursday PM
    assert arena_both.days_of_cover == 3

    heidelberg = plan_delivery(catalog, "heidelberg", SUNDAY_AFTERNOON)
    assert heidelberg.cutoff == datetime(2026, 9, 2, 17, 0)  # Wednesday
    assert heidelberg.days_of_cover == 7


def test_cover_differs_across_vendors_on_the_same_evening(catalog):
    covers = {
        key: plan_delivery(catalog, key, SUNDAY_AFTERNOON).days_of_cover
        for key in ("superior", "columbus_distributing", "arena", "southern_glazers", "sixth_city")
    }
    assert covers["southern_glazers"] == 8
    assert covers["superior"] == 7
    assert len(set(covers.values())) > 1  # a flat 7 would be wrong for at least one


def test_a_vendor_with_no_window_says_where_to_go_instead(catalog):
    with pytest.raises(NoOrderWindow) as excinfo:
        plan_delivery(catalog, "oyo", SUNDAY_AFTERNOON)
    assert "arena" in str(excinfo.value)


def test_upcoming_cutoffs_are_ordered_and_bounded(catalog):
    cutoffs = upcoming_cutoffs(catalog, SUNDAY_AFTERNOON, horizon_days=2)
    times = [cutoff for cutoff, _, _ in cutoffs]
    assert times == sorted(times)
    assert times[0] == datetime(2026, 8, 30, 17, 0)  # Arena, one hour away
    assert all(cutoff <= datetime(2026, 9, 1, 16, 0) for cutoff in times)


def test_cutoff_on_the_window_moment_rolls_to_next_week(catalog):
    """At 19:00 exactly, Superior's Sunday window is still live; a second later it is not."""
    on_time = plan_delivery(catalog, "superior", datetime(2026, 8, 30, 19, 0))
    assert on_time.cutoff == datetime(2026, 8, 30, 19, 0)
    missed = plan_delivery(catalog, "superior", datetime(2026, 8, 30, 19, 1))
    assert missed.cutoff == datetime(2026, 9, 6, 19, 0)
