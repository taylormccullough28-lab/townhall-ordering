"""Days of cover, derived from each vendor's own order windows.

Cover is never a flat seven days. Superior's Monday drop only has to reach
Friday if the Thursday window is used; Southern Glazer's Tuesday drop has to
reach the following Tuesday. Getting this wrong scales every quantity in the
order by 30-100%.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..catalog.loader import Catalog
from ..catalog.models import OrderWindow, Vendor


class NoOrderWindow(ValueError):
    """Raised when a vendor has no window that could carry an order."""


@dataclass(frozen=True)
class DeliveryPlan:
    """The window a manager is ordering into, and what it has to cover."""

    vendor_key: str
    window: OrderWindow
    cutoff: datetime
    delivery: datetime
    next_window: OrderWindow
    next_delivery: datetime
    gap_days: int
    buffer_days: int
    optional_windows_used: bool

    @property
    def days_of_cover(self) -> int:
        """Days this delivery must cover: the gap to the next delivery, plus buffer."""
        return self.gap_days + self.buffer_days

    def to_dict(self) -> dict[str, object]:
        """Machine-readable form for the reasoning record."""
        return {
            "vendor": self.vendor_key,
            "window": self.window.key,
            "cutoff": self.cutoff.isoformat(),
            "delivery": self.delivery.isoformat(),
            "next_window": self.next_window.key,
            "next_delivery": self.next_delivery.isoformat(),
            "gap_days": self.gap_days,
            "buffer_days": self.buffer_days,
            "days_of_cover": self.days_of_cover,
            "optional_windows_used": self.optional_windows_used,
        }


def usable_windows(vendor: Vendor, include_optional: bool) -> list[OrderWindow]:
    """Windows in play for this plan.

    Args:
        vendor: The vendor.
        include_optional: Whether secondary windows (Superior's Thursday,
            Southern Glazer's Wednesday follow-up) count.
    """
    return [w for w in vendor.windows if include_optional or not w.optional]


def plan_delivery(
    catalog: Catalog,
    vendor_key: str,
    at: datetime,
    *,
    include_optional: bool = False,
) -> DeliveryPlan:
    """Work out which window is next, when it lands, and how long it must last.

    Args:
        catalog: Loaded catalog.
        vendor_key: Vendor to plan for.
        at: The moment the manager is ordering.
        include_optional: Whether to assume secondary windows will be used.

    Returns:
        A :class:`DeliveryPlan` whose ``days_of_cover`` drives the forecast.

    Raises:
        NoOrderWindow: If the vendor has no usable window. OYO is the real case
            -- it is ordered as needed through Arena and has none of its own.
    """
    vendor = catalog.vendor(vendor_key)
    windows = usable_windows(vendor, include_optional)
    if not windows:
        routing = (
            f" It routes through {vendor.rules.route_through!r}; plan against that vendor instead."
            if vendor.rules.route_through
            else ""
        )
        raise NoOrderWindow(f"Vendor {vendor_key!r} has no order windows.{routing}")

    upcoming = sorted(((w.next_cutoff(at), w) for w in windows), key=lambda pair: pair[0])
    cutoff, window = upcoming[0]
    delivery = window.delivery_for_cutoff(cutoff)

    following: list[tuple[datetime, OrderWindow]] = []
    for candidate in windows:
        candidate_cutoff = candidate.next_cutoff(cutoff + timedelta(minutes=1))
        candidate_delivery = candidate.delivery_for_cutoff(candidate_cutoff)
        if candidate_delivery > delivery:
            following.append((candidate_delivery, candidate))
    if not following:  # pragma: no cover - a window always recurs weekly
        raise NoOrderWindow(f"Vendor {vendor_key!r} has no delivery after {delivery}.")
    next_delivery, next_window = min(following, key=lambda pair: pair[0])

    return DeliveryPlan(
        vendor_key=vendor_key,
        window=window,
        cutoff=cutoff,
        delivery=delivery,
        next_window=next_window,
        next_delivery=next_delivery,
        gap_days=(next_delivery.date() - delivery.date()).days,
        buffer_days=vendor.rules.cover_buffer_days,
        optional_windows_used=include_optional,
    )


def upcoming_cutoffs(
    catalog: Catalog, at: datetime, *, horizon_days: int = 7
) -> list[tuple[datetime, str, OrderWindow]]:
    """Every vendor cutoff in the next ``horizon_days``, soonest first.

    Feeds the reminder/countdown surface: six encoded windows across four days,
    and missing one costs a week of that vendor's product.
    """
    horizon = at + timedelta(days=horizon_days)
    found: list[tuple[datetime, str, OrderWindow]] = []
    for vendor in catalog.vendors.values():
        for window in vendor.windows:
            cutoff = window.next_cutoff(at)
            if cutoff <= horizon:
                found.append((cutoff, vendor.key, window))
    return sorted(found, key=lambda item: item[0])
