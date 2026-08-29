"""Catalog domain objects: vendors, order windows, products, mappings, recipes.

All of this is loaded from editable YAML under ``thbev/catalog/data``. Nothing
here is hardcoded in Python, because the people who maintain the mapping are not
engineers and the mapping changes every time a keg rotates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Any, Iterable, Sequence

from ..normalize import normalize_key

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


class ConversionType(str, Enum):
    """How a sold menu item turns into vendor units."""

    PACKAGED = "packaged"
    DRAFT = "draft"
    WINE_GLASS = "wine_glass"
    SPIRIT_POUR = "spirit_pour"
    COCKTAIL_RECIPE = "cocktail_recipe"
    WHOLE_BOTTLE = "whole_bottle"
    PREP_INGREDIENT = "prep_ingredient"


#: Conversion types that must never be reached directly from a POS line.
#: A prep ingredient has no menu item of its own -- Chinola and Llords
#: Elderflower are forecast through recipes -- so a direct mapping to one is a
#: catalog error, surfaced rather than silently converted.
INDIRECT_ONLY = frozenset({ConversionType.PREP_INGREDIENT})


@dataclass(frozen=True)
class Contact:
    """Who to reach and how."""

    name: str | None = None
    phone: str | None = None
    email: str | None = None
    label: str | None = None


@dataclass(frozen=True)
class OrderWindow:
    """One ordering cutoff and the delivery it produces.

    Args:
        key: Stable id, e.g. ``"superior_sunday"``.
        order_weekday: 0 = Monday .. 6 = Sunday.
        order_time: Cutoff time on that weekday.
        delivery_weekday: Weekday the resulting delivery lands.
        delivery_time: Nominal delivery time, used only for ordering deliveries
            within a day and for the post-cutoff projection window.
        optional: True for a secondary window the manager may or may not use
            (Superior's Thursday, Southern Glazer's Wednesday follow-up).
        requires_confirmation: True when the window is not guaranteed.
        confirm_with: Who must confirm it.
    """

    key: str
    order_weekday: int
    order_time: time
    delivery_weekday: int
    delivery_time: time = time(9, 0)
    optional: bool = False
    requires_confirmation: bool = False
    confirm_with: str | None = None
    note: str | None = None

    @property
    def lead_days(self) -> int:
        """Whole days from cutoff weekday to delivery weekday (1-7)."""
        delta = (self.delivery_weekday - self.order_weekday) % 7
        return delta or 7

    def next_cutoff(self, after: datetime) -> datetime:
        """First cutoff datetime at or after ``after``."""
        days_ahead = (self.order_weekday - after.weekday()) % 7
        candidate = datetime.combine(after.date() + timedelta(days=days_ahead), self.order_time)
        if candidate < after:
            candidate += timedelta(days=7)
        return candidate

    def delivery_for_cutoff(self, cutoff: datetime) -> datetime:
        """Delivery datetime produced by a given cutoff."""
        return datetime.combine(cutoff.date() + timedelta(days=self.lead_days), self.delivery_time)


@dataclass(frozen=True)
class VendorRules:
    """Vendor-specific behaviour encoded from the order guide."""

    email_only: bool = False
    order_email: str | None = None
    route_through: str | None = None
    routed_contact_hidden_unless: str | None = None
    style_only: bool = False
    style_unit: str | None = None
    keg_return_required: bool = False
    delivery_note: str | None = None
    minimum_order_units: float = 0.0
    #: Extra days a delivery must cover beyond the arithmetic gap to the next
    #: delivery. The PRD states a Southern Glazer's Tuesday drop covers eight
    #: days when the Wednesday follow-up is not placed; Tuesday to Tuesday is
    #: arithmetically seven, so the extra day is carried explicitly here rather
    #: than hidden in the cover calculation.
    cover_buffer_days: int = 0
    emergency_contact: Contact | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Vendor:
    """A distributor, its ordering channel, and its windows."""

    key: str
    name: str
    channel: str
    contact: Contact | None = None
    windows: tuple[OrderWindow, ...] = ()
    rules: VendorRules = field(default_factory=VendorRules)

    def window(self, key: str) -> OrderWindow:
        """Look up one of this vendor's windows by key.

        Raises:
            KeyError: If the vendor has no such window.
        """
        for window in self.windows:
            if window.key == key:
                return window
        raise KeyError(f"Vendor {self.key} has no order window {key!r}.")


@dataclass(frozen=True)
class Product:
    """A vendor SKU or, for rotating lines, a style placeholder.

    Args:
        key: Stable id used by mappings and count sheets.
        name: Human name as the vendor would recognize it.
        vendor: Vendor key, or None when the assignment is not yet confirmed.
        category: Demand category used by event and weather multipliers.
        conversion: How a sale of this product depletes it.
        pack_size: Units per case/pack. Orders round up to this.
        unit_size_oz: Ounces in one sellable container (bottle, keg).
        par: Target on-hand, when known.
        order_critical: Whether this product is on the weekly count list.
        excluded_from_baseline: True for bottle-service SKUs, which are forecast
            from the events calendar instead of trailing sales.
    """

    key: str
    name: str
    vendor: str | None = None
    category: str = "unclassified"
    conversion: ConversionType = ConversionType.PACKAGED
    pack_size: float = 1.0
    unit_size_oz: float | None = None
    unit_label: str = "unit"
    pack_label: str = "case"
    keg_size: str | None = None
    default_pour_oz: float | None = None
    par: float | None = None
    order_critical: bool = False
    excluded_from_baseline: bool = False
    max_order_units: float | None = None
    vendor_confidence: str = "unconfirmed"
    style: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RecipeLine:
    """One ingredient of a cocktail or bundle."""

    product: str
    oz: float | None = None
    units: float | None = None

    def amount(self) -> tuple[str, float]:
        """Return ``(kind, amount)`` where kind is ``"oz"`` or ``"units"``.

        Raises:
            ValueError: If neither or both of oz/units are set.
        """
        if (self.oz is None) == (self.units is None):
            raise ValueError(
                f"Recipe line for {self.product!r} must set exactly one of oz or units."
            )
        return ("oz", float(self.oz)) if self.oz is not None else ("units", float(self.units))


@dataclass(frozen=True)
class Recipe:
    """A named build: cocktail spec, or a bottle-service package's bundle."""

    key: str
    lines: tuple[RecipeLine, ...]
    description: str | None = None


@dataclass(frozen=True)
class MappingKey:
    """Composite POS key. ``None`` on a part means "any value".

    A null part is an explicit authoring choice recorded in the catalog, not an
    implicit fallback: the resolver never matches on item name alone unless a
    mapping entry says to.
    """

    sales_category: str | None = None
    menu: str | None = None
    menu_group: str | None = None
    menu_item: str | None = None

    @property
    def normalized(self) -> tuple[str | None, str | None, str | None, str | None]:
        return tuple(  # type: ignore[return-value]
            normalize_key(part) if part is not None else None
            for part in (self.sales_category, self.menu, self.menu_group, self.menu_item)
        )

    @property
    def specificity(self) -> int:
        """How many parts are constrained. Higher wins when several match."""
        return sum(1 for part in self.normalized if part is not None)

    def __str__(self) -> str:  # pragma: no cover - display only
        parts = [
            self.sales_category or "*",
            self.menu or "*",
            self.menu_group or "*",
            self.menu_item or "*",
        ]
        return " | ".join(parts)


@dataclass(frozen=True)
class Mapping:
    """Binds a POS item to product depletion.

    Exactly one of ``product`` or ``recipe`` is set. ``pour_oz`` overrides the
    default pour for spirit and draft conversions; ``bundle`` names a recipe of
    mixers that deplete alongside a whole bottle.
    """

    key: MappingKey
    product: str | None = None
    recipe: str | None = None
    factor: float = 1.0
    pour_oz: float | None = None
    bundle: str | None = None
    conversion: ConversionType | None = None
    bottle_service: bool = False
    notes: list[str] = field(default_factory=list)

    def matches(self, item_key: Sequence[str]) -> bool:
        """True when every constrained part of this mapping equals the sale's part."""
        for constraint, actual in zip(self.normalized_parts, item_key):
            if constraint is None:
                continue
            if constraint != actual:
                return False
        return True

    @property
    def normalized_parts(self) -> tuple[str | None, ...]:
        return self.key.normalized


@dataclass(frozen=True)
class PourSizes:
    """House pour sizes, in ounces."""

    single: float = 1.5
    rocks: float = 2.5
    double: float = 3.0
    default: str = "single"
    #: Normalized modifier text -> pour name.
    modifier_aliases: dict[str, str] = field(default_factory=dict)

    def size_for(self, pour_name: str | None) -> float:
        """Ounces for a pour name, falling back to the configured default.

        Raises:
            KeyError: If an explicit, unknown pour name is given.
        """
        name = (pour_name or self.default).lower()
        if not hasattr(self, name):
            raise KeyError(f"Unknown pour {pour_name!r}; known pours: single, rocks, double.")
        return float(getattr(self, name))

    def resolve_modifier(self, modifier: str) -> str | None:
        """Map a POS modifier string to a pour name, or None if it is not a pour."""
        return self.modifier_aliases.get(normalize_key(modifier))


@dataclass(frozen=True)
class BottleYields:
    """Theoretical ounces per container, before overpour."""

    ml_750: float = 25.36
    ml_1000: float = 33.81
    ml_1750: float = 59.17
    half_barrel_oz: float = 1880.0
    sixth_barrel_oz: float = 627.0


@dataclass
class EngineConfig:
    """Everything tunable, loaded from ``config.yaml``."""

    location: str = "Townhall - Short North"
    business_day_cutoff_hour: int = 4
    pours: PourSizes = field(default_factory=PourSizes)
    yields: BottleYields = field(default_factory=BottleYields)
    overpour_factor: float = 0.05
    wine_glass_oz: float = 5.0
    draft_pour_oz: float = 16.0
    safety_stock_fraction: float = 0.25
    safety_stock_floor: float = 1.0
    baseline_weeks: int = 4
    baseline_trim: str = "high_low"
    event_multipliers: dict[str, Any] = field(default_factory=dict)
    weather_multipliers: dict[str, Any] = field(default_factory=dict)
    buyout_per_head_units: dict[str, float] = field(default_factory=dict)
    superior_second_window_threshold: float = 0.20
    post_cutoff_fallback: str = "error"

    def effective_yield_oz(self, container_oz: float) -> float:
        """Apply the overpour factor: ``theoretical / (1 + overpour)``."""
        return container_oz / (1.0 + self.overpour_factor)


def weekday_index(value: Any) -> int:
    """Convert a weekday name or number to 0=Monday..6=Sunday.

    Raises:
        ValueError: If the value is not a recognized weekday.
    """
    if isinstance(value, int):
        if 0 <= value <= 6:
            return value
        raise ValueError(f"Weekday index {value} out of range 0-6.")
    text = str(value).strip().lower()
    if text in WEEKDAYS:
        return WEEKDAYS.index(text)
    for index, name in enumerate(WEEKDAYS):
        if name.startswith(text[:3]):
            return index
    raise ValueError(f"Unrecognized weekday {value!r}.")


def parse_time(value: Any) -> time:
    """Parse ``"19:00"``, ``"7:00 PM"`` or a ``datetime.time``.

    Raises:
        ValueError: If the value cannot be parsed.
    """
    if isinstance(value, time):
        return value
    text = str(value).strip().upper().replace(".", "")
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I %p", "%I:%M%p"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized time {value!r}; use 24-hour 'HH:MM'.")


def weekday_name(index: int) -> str:
    """Human name for a weekday index."""
    return WEEKDAYS[index].capitalize()


def next_weekday_datetime(after: datetime, weekday: int, at: time) -> datetime:
    """First datetime strictly at or after ``after`` on ``weekday`` at ``at``."""
    days_ahead = (weekday - after.weekday()) % 7
    candidate = datetime.combine(after.date() + timedelta(days=days_ahead), at)
    if candidate < after:
        candidate += timedelta(days=7)
    return candidate


def date_weekday_name(value: date) -> str:
    """Weekday name for a date."""
    return weekday_name(value.weekday())


def iter_products(products: Iterable[Product], vendor: str | None) -> list[Product]:
    """Products belonging to one vendor key."""
    return [p for p in products if p.vendor == vendor]
