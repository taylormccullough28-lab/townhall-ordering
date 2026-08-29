"""Business-day arithmetic.

TownHall's business day closes at 4:00 AM. A sale rung at 01:30 belongs to the
*prior* calendar day's business. Every date bucket in this package -- trailing
weekday baselines, post-cutoff projections, ingest date-range filters -- goes
through :func:`business_day_of` so the boundary is defined in exactly one place.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

DEFAULT_CUTOFF_HOUR = 4


def business_day_of(timestamp: datetime, cutoff_hour: int = DEFAULT_CUTOFF_HOUR) -> date:
    """Return the business date a timestamp belongs to.

    Args:
        timestamp: Wall-clock local time of the sale.
        cutoff_hour: Hour (0-23) at which the business day rolls over. 4 means
            "business day ends at 4:00 AM"; 03:59 belongs to the prior day and
            04:00 starts a new one.

    Returns:
        The calendar date of the business day.

    Raises:
        ValueError: If ``cutoff_hour`` is outside 0-23.
    """
    if not 0 <= cutoff_hour <= 23:
        raise ValueError(f"cutoff_hour must be 0-23, got {cutoff_hour}")
    if timestamp.hour < cutoff_hour:
        return (timestamp - timedelta(days=1)).date()
    return timestamp.date()


def business_day_bounds(
    business_date: date, cutoff_hour: int = DEFAULT_CUTOFF_HOUR
) -> tuple[datetime, datetime]:
    """Return the half-open ``[start, end)`` wall-clock span of a business day.

    A business date of 2026-08-30 with a 4 AM cutoff spans
    2026-08-30 04:00 through 2026-08-31 04:00.
    """
    start = datetime.combine(business_date, datetime.min.time()).replace(hour=cutoff_hour)
    return start, start + timedelta(days=1)


def business_days_between(start: date, end: date) -> list[date]:
    """Inclusive list of business dates from ``start`` to ``end``."""
    if end < start:
        raise ValueError(f"end {end} precedes start {start}")
    days = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += timedelta(days=1)
    return days


def hour_slot(timestamp: datetime, cutoff_hour: int = DEFAULT_CUTOFF_HOUR) -> int:
    """Return the 0-23 offset of a timestamp within its business day.

    Slot 0 is the cutoff hour itself (04:00-04:59 for a 4 AM close), slot 23 is
    the final hour before the next rollover (03:00-03:59). Used to build the
    hourly sales profile that prorates post-cutoff projections.
    """
    return (timestamp.hour - cutoff_hour) % 24
