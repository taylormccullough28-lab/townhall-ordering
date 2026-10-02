"""Baseline demand, event/weather multipliers, and the post-cutoff projection.

Three pieces:

* :class:`BaselineModel` -- trailing 4-week mean by weekday, outlier-trimmed.
  Bottle service is excluded here on purpose: one buyout can move more Grey
  Goose in a night than a normal month of cocktails, and leaving it in the
  average inflates a premium spirit's forecast for a month.
* :class:`MultiplierEngine` -- the editable event and weather coefficients.
* :class:`HourlyProfile` / :func:`project_sales` -- the post-cutoff adjustment,
  which needs timestamped sales and therefore refuses to run on PMIX.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Iterable, Sequence

from ..catalog.models import EngineConfig, Product
from ..depletion.engine import DepletionResult
from ..timeutil import business_day_of, hour_slot


class ForecastError(ValueError):
    """Raised when a forecast is requested that the data cannot support."""


class PostCutoffUnavailable(ForecastError):
    """Raised when the post-cutoff adjustment has no time dimension to work from."""


@dataclass
class Weather:
    """A day's weather read, manual or pulled."""

    high_f: float | None = None
    sunny: bool = False


@dataclass
class Buyout:
    """A private buyout, which overrides the baseline for its day."""

    headcount: int
    label: str = "Private buyout"


@dataclass
class DayContext:
    """Everything that scales one future day's demand."""

    day: date
    events: list[str] = field(default_factory=list)
    weather: Weather | None = None
    buyout: Buyout | None = None
    #: product key -> multiplier, for a feature or promo on a specific item.
    promos: dict[str, float] = field(default_factory=dict)


@dataclass
class AppliedMultiplier:
    """One coefficient that was applied, kept for the reasoning record."""

    driver: str
    label: str
    factor: float

    def to_dict(self) -> dict[str, object]:
        return {"driver": self.driver, "label": self.label, "factor": round(self.factor, 4)}


@dataclass
class DayForecast:
    """The forecast for one product on one day, with its arithmetic exposed."""

    day: date
    baseline: float
    multipliers: list[AppliedMultiplier]
    units: float
    overridden_by: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "day": self.day.isoformat(),
            "weekday": self.day.strftime("%A"),
            "baseline": round(self.baseline, 4),
            "multipliers": [m.to_dict() for m in self.multipliers],
            "units": round(self.units, 4),
            "overridden_by": self.overridden_by,
        }


class BaselineModel:
    """Trailing weekday means built from depletion history.

    Args:
        daily_units: ``{(product_key, business_date): units}``.
        open_days: Every business date the bar was actually open in the history
            window. A day with no sale of an item counts as a zero for that
            item -- without this, a slow SKU's mean is computed only over the
            days it happened to sell and comes out far too high.
        weeks: How many same-weekday observations to keep.
        trim: ``"high_low"`` drops the single highest and lowest when at least
            four observations exist; ``"none"`` disables trimming.
    """

    def __init__(
        self,
        daily_units: dict[tuple[str, date], float],
        open_days: Iterable[date],
        *,
        weeks: int = 4,
        trim: str = "high_low",
    ) -> None:
        self.daily_units = dict(daily_units)
        self.open_days = sorted(set(open_days))
        self.weeks = weeks
        self.trim = trim
        self._by_weekday: dict[int, list[date]] = defaultdict(list)
        for day in self.open_days:
            self._by_weekday[day.weekday()].append(day)

    def observations(self, product_key: str, weekday: int, as_of: date | None = None) -> list[float]:
        """Units observed for a product on a weekday, most recent last."""
        days = [d for d in self._by_weekday.get(weekday, []) if as_of is None or d < as_of]
        recent = days[-self.weeks :]
        return [self.daily_units.get((product_key, day), 0.0) for day in recent]

    def baseline(self, product_key: str, weekday: int, as_of: date | None = None) -> float:
        """Trimmed mean units for a product on a weekday.

        Returns 0.0 when there is no history at all for that weekday; the caller
        reports the absence rather than the model inventing a number.
        """
        values = self.observations(product_key, weekday, as_of)
        return trimmed_mean(values, self.trim)

    def weeks_of_history(self, weekday: int) -> int:
        """How many same-weekday observations the model actually has."""
        return min(len(self._by_weekday.get(weekday, [])), self.weeks)


def trimmed_mean(values: Sequence[float], trim: str = "high_low") -> float:
    """Mean with the single highest and lowest value dropped when n >= 4.

    Args:
        values: Observations.
        trim: ``"high_low"`` or ``"none"``.

    Raises:
        ValueError: If ``trim`` is not a known strategy.
    """
    if not values:
        return 0.0
    if trim == "none":
        return sum(values) / len(values)
    if trim != "high_low":
        raise ValueError(f"Unknown baseline trim strategy {trim!r}; use 'high_low' or 'none'.")
    if len(values) < 4:
        return sum(values) / len(values)
    ordered = sorted(values)[1:-1]
    return sum(ordered) / len(ordered)


class MultiplierEngine:
    """Applies the editable event, weather and promo coefficients."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    def for_day(self, product: Product, context: DayContext) -> list[AppliedMultiplier]:
        """Every multiplier that applies to this product on this day.

        Raises:
            ForecastError: If a configured event key is unknown.
        """
        applied: list[AppliedMultiplier] = []
        for event_key in context.events:
            spec = self.config.event_multipliers.get(event_key)
            if spec is None:
                raise ForecastError(
                    f"Unknown event {event_key!r}. Known events: "
                    f"{', '.join(sorted(self.config.event_multipliers)) or '(none configured)'}."
                )
            if spec.get("overrides_baseline"):
                continue
            factor = self._category_factor(spec, product.category)
            if factor is not None and factor != 1.0:
                applied.append(AppliedMultiplier(event_key, spec.get("label", event_key), factor))

        if context.weather is not None:
            for weather_key, spec in self.config.weather_multipliers.items():
                if not self._weather_applies(spec, context.weather):
                    continue
                factor = self._category_factor(spec, product.category)
                if factor is not None and factor != 1.0:
                    applied.append(
                        AppliedMultiplier(weather_key, spec.get("label", weather_key), factor)
                    )

        promo = context.promos.get(product.key)
        if promo is not None and promo != 1.0:
            applied.append(AppliedMultiplier("promo", f"Promo on {product.name}", float(promo)))
        return applied

    @staticmethod
    def _category_factor(spec: dict, category: str) -> float | None:
        categories = spec.get("categories") or {}
        if category in categories:
            return float(categories[category])
        if "overall" in spec:
            return float(spec["overall"])
        return None

    @staticmethod
    def _weather_applies(spec: dict, weather: Weather) -> bool:
        if weather.high_f is None:
            return False
        minimum = spec.get("threshold_f_min")
        maximum = spec.get("threshold_f_max")
        if minimum is not None and weather.high_f <= float(minimum):
            return False
        if maximum is not None and weather.high_f >= float(maximum):
            return False
        if spec.get("requires_sunny") and not weather.sunny:
            return False
        return True

    def buyout_units(self, product: Product, buyout: Buyout) -> float:
        """Units a buyout is expected to move for this product.

        Raises:
            ForecastError: If no per-head rate is configured for the product's
                category. The PRD specifies the formula but no rates, so the
                engine says so rather than forecasting a silent zero.
        """
        rates = self.config.buyout_per_head_units or {}
        if product.category not in rates and product.key not in rates:
            raise ForecastError(
                f"A private buyout is on the calendar but no per-head rate is configured for "
                f"{product.name} (category {product.category!r}). Set buyout_per_head_units in "
                "config.yaml -- the PRD gives the formula (headcount x per-head rate) but no rates."
            )
        rate = float(rates.get(product.key, rates.get(product.category, 0.0)))
        return buyout.headcount * rate


@dataclass
class ProductForecast:
    """A product's forecast across the cover window."""

    product_key: str
    days: list[DayForecast]

    @property
    def total(self) -> float:
        return sum(day.units for day in self.days)

    def to_dict(self) -> dict[str, object]:
        return {
            "product": self.product_key,
            "total_units": round(self.total, 4),
            "days": [day.to_dict() for day in self.days],
        }


def forecast_product(
    product: Product,
    contexts: Sequence[DayContext],
    baseline: BaselineModel,
    multipliers: MultiplierEngine,
    *,
    as_of: date | None = None,
) -> ProductForecast:
    """Forecast one product over a run of days.

    Bottle-service products carry ``excluded_from_baseline``; for those the
    trailing mean is not used at all and the forecast comes from booked events.

    Raises:
        ForecastError: If an event or buyout cannot be evaluated.
    """
    days: list[DayForecast] = []
    for context in contexts:
        if context.buyout is not None:
            units = multipliers.buyout_units(product, context.buyout)
            days.append(
                DayForecast(
                    day=context.day,
                    baseline=0.0,
                    multipliers=[],
                    units=units,
                    overridden_by=context.buyout.label,
                )
            )
            continue

        if product.excluded_from_baseline:
            # Bottle service: no trailing baseline. Demand comes from bookings,
            # which arrive as promos/explicit units on the day context.
            booked = float(context.promos.get(product.key, 0.0))
            days.append(
                DayForecast(
                    day=context.day,
                    baseline=0.0,
                    multipliers=[],
                    units=booked,
                    overridden_by="events calendar (excluded from trailing baseline)",
                )
            )
            continue

        base = baseline.baseline(product.key, context.day.weekday(), as_of)
        applied = multipliers.for_day(product, context)
        units = base
        for multiplier in applied:
            units *= multiplier.factor
        days.append(DayForecast(day=context.day, baseline=base, multipliers=applied, units=units))
    return ProductForecast(product_key=product.key, days=days)


class HourlyProfile:
    """When during a business day a product actually sells.

    Built from timestamped sales. Slot 0 is the hour starting at the business-day
    cutoff (04:00-04:59 for a 4 AM close) and slot 23 is 03:00-03:59.
    """

    def __init__(self, weights: Sequence[float], cutoff_hour: int, sample_size: int) -> None:
        if len(weights) != 24:
            raise ValueError("An hourly profile needs exactly 24 slot weights.")
        total = sum(weights)
        if total <= 0:
            raise ValueError("An hourly profile needs at least one non-zero slot.")
        self.weights = [w / total for w in weights]
        self.cutoff_hour = cutoff_hour
        self.sample_size = sample_size

    @classmethod
    def from_depletion(
        cls,
        depletion: DepletionResult,
        cutoff_hour: int,
        *,
        product_key: str | None = None,
        minimum_sample: int = 10,
    ) -> "HourlyProfile":
        """Build a profile from timestamped depletion lines.

        Args:
            depletion: Depletion whose lines carry ``sold_at``.
            cutoff_hour: Business-day rollover hour.
            product_key: Build a per-product profile; None pools every product,
                which is the sensible fallback for a slow SKU.
            minimum_sample: Fewest timestamped lines that will produce a profile.

        Raises:
            PostCutoffUnavailable: If there are too few timestamped lines. PMIX
                has no time dimension at all, so this is the expected failure
                when only a PMIX was uploaded.
        """
        slots = [0.0] * 24
        sample = 0
        for line in depletion.lines:
            if line.sold_at is None:
                continue
            if product_key is not None and line.product_key != product_key:
                continue
            slots[hour_slot(line.sold_at, cutoff_hour)] += line.units
            sample += 1
        if sample < minimum_sample or sum(slots) <= 0:
            raise PostCutoffUnavailable(
                f"Not enough timestamped sales to build an hourly profile "
                f"({sample} lines; {minimum_sample} needed"
                + (f" for product {product_key!r}" if product_key else "")
                + "). PMIX is aggregated and carries no time dimension -- the post-cutoff "
                "adjustment needs an ItemSelectionDetails export."
            )
        return cls(slots, cutoff_hour, sample)

    def fraction_between(self, start: datetime, end: datetime) -> float:
        """Fraction of one business day's volume falling between two times.

        Both bounds are treated as wall-clock times inside a single business
        day; hours are prorated linearly within a slot.
        """
        if end <= start:
            return 0.0
        total = 0.0
        cursor = start
        while cursor < end:
            slot_end = (cursor + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            segment_end = min(slot_end, end)
            share = (segment_end - cursor).total_seconds() / 3600.0
            total += self.weights[hour_slot(cursor, self.cutoff_hour)] * share
            cursor = segment_end
        return total

    def remaining_fraction(self, at: datetime) -> float:
        """Fraction of the business day's volume still to come after ``at``."""
        from ..timeutil import business_day_bounds

        _, end = business_day_bounds(business_day_of(at, self.cutoff_hour), self.cutoff_hour)
        return self.fraction_between(at, end)


@dataclass
class PostCutoffProjection:
    """Projected sales between an order cutoff and its delivery."""

    product_key: str
    units: float
    from_time: datetime
    to_time: datetime
    detail: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return {
            "product": self.product_key,
            "units": round(self.units, 4),
            "from": self.from_time.isoformat(),
            "to": self.to_time.isoformat(),
            "detail": self.detail,
        }


def project_sales(
    product: Product,
    start: datetime,
    end: datetime,
    baseline: BaselineModel,
    multipliers: MultiplierEngine,
    profile: HourlyProfile,
    *,
    contexts: dict[date, DayContext] | None = None,
    cutoff_hour: int = 4,
) -> PostCutoffProjection:
    """Project sales in the window between an order cutoff and its delivery.

    This is the adjustment that stops the system under-ordering every Sunday and
    Monday: an order placed at 5 PM Sunday is placed while the bar is still
    selling, and the truck does not land until Monday morning.

    ``effective_on_hand = counted_on_hand - projected_sales(cutoff -> delivery)``

    Args:
        product: Product to project.
        start: Order cutoff (or count time).
        end: Delivery time.
        baseline: Trailing weekday model.
        multipliers: Event/weather coefficients.
        profile: Hourly sales shape, from timestamped data.
        contexts: Per-day event context, keyed by business date.
        cutoff_hour: Business-day rollover.

    Returns:
        A :class:`PostCutoffProjection` with a per-day breakdown.
    """
    from ..timeutil import business_day_bounds

    contexts = contexts or {}
    total = 0.0
    detail: list[dict[str, object]] = []
    day = business_day_of(start, cutoff_hour)
    last_day = business_day_of(end, cutoff_hour)
    while day <= last_day:
        day_start, day_end = business_day_bounds(day, cutoff_hour)
        window_start = max(day_start, start)
        window_end = min(day_end, end)
        if window_end > window_start:
            base = baseline.baseline(product.key, day.weekday())
            context = contexts.get(day, DayContext(day=day))
            applied = multipliers.for_day(product, context)
            expected_day = base
            for multiplier in applied:
                expected_day *= multiplier.factor
            fraction = profile.fraction_between(window_start, window_end)
            units = expected_day * fraction
            total += units
            detail.append(
                {
                    "day": day.isoformat(),
                    "from": window_start.isoformat(),
                    "to": window_end.isoformat(),
                    "day_forecast_units": round(expected_day, 4),
                    "fraction_of_day": round(fraction, 4),
                    "units": round(units, 4),
                    "multipliers": [m.to_dict() for m in applied],
                }
            )
        day += timedelta(days=1)
    return PostCutoffProjection(product.key, total, start, end, detail)
