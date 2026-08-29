"""The order suggestion engine.

::

    days_of_cover = days until this vendor's NEXT delivery (never a flat 7)
    forecast       = sum over the cover window of baseline x multipliers
    safety         = 25% of forecast, floored at 1 unit
    effective_on_hand = counted_on_hand - projected_sales(cutoff -> delivery)
    need           = forecast + safety - effective_on_hand - already_on_order
    order_qty      = round_up_to_pack(need), subject to vendor minimum

Every suggested quantity carries a :class:`ReasoningRecord` -- what sold, which
multipliers fired, what was counted, how many days it has to cover, and how the
arithmetic landed -- because a number nobody can check is a number nobody will
trust.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Iterable, Sequence

from ..catalog.loader import Catalog
from ..catalog.models import Product, Vendor
from ..depletion.engine import DepletionResult, packs_for_units
from .cover import DeliveryPlan, NoOrderWindow, plan_delivery
from .forecast import (
    BaselineModel,
    DayContext,
    HourlyProfile,
    MultiplierEngine,
    PostCutoffUnavailable,
    ProductForecast,
    forecast_product,
    project_sales,
)


@dataclass
class ReasoningRecord:
    """Machine-readable justification for one suggested quantity."""

    product_key: str
    product_name: str
    vendor_key: str | None
    units_sold_last_week: float
    baseline_by_weekday: dict[str, float]
    forecast: ProductForecast
    forecast_over_cover: float
    safety_stock: float
    counted_on_hand: float
    post_cutoff: dict[str, object]
    effective_on_hand: float
    already_on_order: float
    need_units: float
    pack_size: float
    order_packs: int
    order_units: float
    days_of_cover: int
    plan: dict[str, object]
    caps: dict[str, object] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """Full record, suitable for storing against the order."""
        return {
            "product": self.product_key,
            "product_name": self.product_name,
            "vendor": self.vendor_key,
            "units_sold_last_week": round(self.units_sold_last_week, 4),
            "baseline_by_weekday": {k: round(v, 4) for k, v in self.baseline_by_weekday.items()},
            "days_of_cover": self.days_of_cover,
            "delivery_plan": self.plan,
            "forecast": self.forecast.to_dict(),
            "forecast_over_cover": round(self.forecast_over_cover, 4),
            "safety_stock": round(self.safety_stock, 4),
            "counted_on_hand": round(self.counted_on_hand, 4),
            "post_cutoff_adjustment": self.post_cutoff,
            "effective_on_hand": round(self.effective_on_hand, 4),
            "already_on_order": round(self.already_on_order, 4),
            "need_units": round(self.need_units, 4),
            "pack_size": self.pack_size,
            "order_packs": self.order_packs,
            "order_units": round(self.order_units, 4),
            "caps": self.caps,
            "notes": list(self.notes),
        }

    def one_liner(self) -> str:
        """The single explanatory line the PRD asks for on every quantity."""
        drivers = []
        for day in self.forecast.days:
            for multiplier in day.multipliers:
                drivers.append(f"{multiplier.label} x{multiplier.factor:g}")
        driver_text = f", {'; '.join(sorted(set(drivers)))}" if drivers else ""
        return (
            f"{self.product_name}: sold {self.units_sold_last_week:.1f} last week"
            f"{driver_text}; forecast {self.forecast_over_cover:.1f} over "
            f"{self.days_of_cover} days of cover, safety {self.safety_stock:.1f}, "
            f"on hand {self.effective_on_hand:.1f}, on order {self.already_on_order:g} "
            f"-> order {self.order_packs} x {self.pack_size:g}"
        )


@dataclass
class OrderLine:
    """One suggested product quantity."""

    product: Product
    order_packs: int
    order_units: float
    reasoning: ReasoningRecord
    override_packs: int | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def final_packs(self) -> int:
        """The quantity that will actually be sent: the override if one exists."""
        return self.override_packs if self.override_packs is not None else self.order_packs

    def to_dict(self) -> dict[str, object]:
        return {
            "product": self.product.key,
            "name": self.product.name,
            "pack_label": self.product.pack_label,
            "pack_size": self.product.pack_size,
            "suggested_packs": self.order_packs,
            "override_packs": self.override_packs,
            "final_packs": self.final_packs,
            "reasoning": self.reasoning.to_dict(),
            "reasoning_line": self.reasoning.one_liner(),
            "warnings": list(self.warnings),
        }


@dataclass
class StyleRecommendation:
    """A style-and-count recommendation for a rotating line, with no SKU.

    Sixth City and Cavalier rotate constantly; naming a product would be a
    guess the rep has to correct.
    """

    vendor_key: str
    count: int
    unit: str
    styles: list[str]
    ask: str
    reasoning: list[ReasoningRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "vendor": self.vendor_key,
            "count": self.count,
            "unit": self.unit,
            "styles": list(self.styles),
            "ask": self.ask,
            "reasoning": [r.to_dict() for r in self.reasoning],
        }

    def text(self) -> str:
        """The line a manager reads to the rep."""
        styles = ", ".join(self.styles) if self.styles else "rep's choice"
        return f"{self.count} x {self.unit}, {styles} - {self.ask}"


@dataclass
class VendorOrder:
    """A complete suggestion for one vendor, shaped by that vendor's rules."""

    vendor: Vendor
    plan: DeliveryPlan
    lines: list[OrderLine] = field(default_factory=list)
    style_recommendations: list[StyleRecommendation] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    window_recommendation: dict[str, object] | None = None
    follow_up_offer: dict[str, object] | None = None
    routed_from: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "vendor": self.vendor.key,
            "vendor_name": self.vendor.name,
            "channel": self.vendor.channel,
            "delivery_plan": self.plan.to_dict(),
            "lines": [line.to_dict() for line in self.lines],
            "style_recommendations": [s.to_dict() for s in self.style_recommendations],
            "notes": list(self.notes),
            "warnings": list(self.warnings),
            "window_recommendation": self.window_recommendation,
            "follow_up_offer": self.follow_up_offer,
            "routed_from": list(self.routed_from),
            "empty_keg_return_required": self.vendor.rules.keg_return_required,
        }


class OrderEngine:
    """Builds per-vendor order suggestions from depletion history."""

    def __init__(
        self,
        catalog: Catalog,
        depletion: DepletionResult,
        *,
        open_days: Iterable[date] | None = None,
    ) -> None:
        """Args:
        catalog: Vendors, products, mappings and config.
        depletion: Converted sales history.
        open_days: Business dates the bar was open. Defaults to every date
            present in the depletion history, which is right when the ingest
            covers a complete week.
        """
        self.catalog = catalog
        self.config = catalog.config
        self.depletion = depletion
        daily = depletion.daily_units(include_bottle_service=False)
        self.open_days = sorted(set(open_days) if open_days is not None else {d for _, d in daily})
        self.baseline = BaselineModel(
            daily,
            self.open_days,
            weeks=self.config.baseline_weeks,
            trim=self.config.baseline_trim,
        )
        self.multipliers = MultiplierEngine(self.config)
        self._daily = daily

    # -- helpers --------------------------------------------------------------

    def units_sold_last_week(self, product_key: str) -> float:
        """Units depleted over the last seven open business days of history."""
        recent = self.open_days[-7:]
        return sum(self._daily.get((product_key, day), 0.0) for day in recent)

    def hourly_profile(self, product_key: str) -> HourlyProfile:
        """Per-product hourly shape, falling back to the pooled shape.

        Raises:
            PostCutoffUnavailable: If there is no timestamped history at all.
        """
        try:
            return HourlyProfile.from_depletion(
                self.depletion, self.config.business_day_cutoff_hour, product_key=product_key
            )
        except PostCutoffUnavailable:
            return HourlyProfile.from_depletion(
                self.depletion, self.config.business_day_cutoff_hour
            )

    def cover_days(self, plan: DeliveryPlan) -> list[date]:
        """Business dates the incoming delivery has to carry."""
        first = plan.delivery.date()
        return [first + timedelta(days=offset) for offset in range(plan.days_of_cover)]

    def vendor_products(self, vendor_key: str) -> tuple[list[Product], list[str]]:
        """Products to order from a vendor, including anything routed through it.

        Returns ``(products, routed_from_vendor_keys)``.
        """
        products = list(self.catalog.products_for_vendor(vendor_key))
        routed: list[str] = []
        for vendor in self.catalog.vendors.values():
            if vendor.rules.route_through == vendor_key:
                extra = self.catalog.products_for_vendor(vendor.key)
                if extra:
                    products.extend(extra)
                routed.append(vendor.key)
        return products, routed

    # -- the calculation ------------------------------------------------------

    def suggest_vendor(
        self,
        vendor_key: str,
        *,
        at: datetime,
        on_hand: dict[str, float] | None = None,
        on_order: dict[str, float] | None = None,
        calendar: dict[date, DayContext] | None = None,
        include_optional_windows: bool = False,
        counted_at: datetime | None = None,
        overrides: dict[str, int] | None = None,
        strict_post_cutoff: bool = False,
        _skip_vendor_rules: bool = False,
    ) -> VendorOrder:
        """Suggest an order for one vendor.

        Args:
            vendor_key: Vendor to order from.
            at: The moment the manager is ordering; picks the window.
            on_hand: Counted units per product key, from the order-critical count.
            on_order: Units already ordered and not yet delivered.
            calendar: Per-business-date event/weather context.
            include_optional_windows: Assume secondary windows are used, which
                shortens the cover.
            counted_at: When the count was taken. The post-cutoff projection runs
                from here (or from the cutoff) to the delivery.
            overrides: Manager overrides, in packs, per product key.
            strict_post_cutoff: Raise instead of warning when the sales data has
                no time dimension.

        Returns:
            A :class:`VendorOrder`.

        Raises:
            NoOrderWindow: If the vendor has no window and does not route
                through one that does.
            ForecastError: If the calendar references an unknown event, or a
                buyout has no configured per-head rate.
        """
        vendor = self.catalog.vendor(vendor_key)
        on_hand = on_hand or {}
        on_order = on_order or {}
        calendar = calendar or {}
        overrides = overrides or {}

        planning_vendor = vendor
        routed_note: str | None = None
        if vendor.rules.route_through:
            planning_vendor = self.catalog.vendor(vendor.rules.route_through)
            routed_note = (
                f"{vendor.name} routes through {planning_vendor.name}. "
                f"{planning_vendor.name} is the first call."
            )

        plan = plan_delivery(
            self.catalog, planning_vendor.key, at, include_optional=include_optional_windows
        )
        order = VendorOrder(vendor=vendor, plan=plan)
        if routed_note:
            order.notes.append(routed_note)

        products, routed_from = self.vendor_products(vendor_key)
        order.routed_from = routed_from
        if routed_from:
            order.notes.append(
                "Includes products routed through this vendor: " + ", ".join(routed_from) + "."
            )
        if not products:
            order.warnings.append(
                f"No products in the catalog are assigned to {vendor.name}. "
                "Assign vendors in products.yaml -- until then this order sheet is empty."
            )

        contexts = [calendar.get(day, DayContext(day=day)) for day in self.cover_days(plan)]
        projection_start = counted_at or plan.cutoff

        profile_error: str | None = None
        for product in sorted(products, key=lambda p: p.name):
            # A per-product hourly shape where the SKU has enough timestamped
            # sales, otherwise the pooled shape across every product.
            profile: HourlyProfile | None
            try:
                profile = self.hourly_profile(product.key)
            except PostCutoffUnavailable as exc:
                profile = None
                profile_error = str(exc)
                if strict_post_cutoff:
                    raise
            line = self._suggest_line(
                product=product,
                vendor=vendor,
                plan=plan,
                contexts=contexts,
                on_hand=float(on_hand.get(product.key, 0.0)),
                on_order=float(on_order.get(product.key, 0.0)),
                calendar=calendar,
                projection_start=projection_start,
                profile=profile,
                profile_error=profile_error,
            )
            if product.key in overrides:
                line.override_packs = int(overrides[product.key])
            order.lines.append(line)

        if profile_error:
            order.warnings.append(
                "Post-cutoff depletion adjustment did not run: " + profile_error.split(".")[0]
                + ". Counted on-hand was used as-is, which under-orders any window that "
                "closes while the bar is still selling (Sunday 5-7 PM, Monday 4-5 PM)."
            )

        if not _skip_vendor_rules:
            from .vendor_rules import apply_vendor_rules

            apply_vendor_rules(self, order, at=at, calendar=calendar, on_hand=on_hand,
                               on_order=on_order, counted_at=counted_at, overrides=overrides)
        return order

    def suggest_all(self, **kwargs) -> list[VendorOrder]:
        """Suggest orders for every vendor that has products or a window.

        Vendors with no usable window and no routing are skipped with a note in
        the returned orders' warnings.
        """
        orders: list[VendorOrder] = []
        for vendor_key in self.catalog.vendors:
            try:
                orders.append(self.suggest_vendor(vendor_key, **kwargs))
            except NoOrderWindow:
                continue
        return orders

    def _suggest_line(
        self,
        *,
        product: Product,
        vendor: Vendor,
        plan: DeliveryPlan,
        contexts: Sequence[DayContext],
        on_hand: float,
        on_order: float,
        calendar: dict[date, DayContext],
        projection_start: datetime,
        profile: HourlyProfile | None,
        profile_error: str | None,
    ) -> OrderLine:
        forecast = forecast_product(product, contexts, self.baseline, self.multipliers)
        forecast_over_cover = forecast.total
        # PRD: "safety = 25% of forecast_over_cover, floored at 1 unit". The floor
        # is applied literally, including to items with no forecast at all -- for
        # those it means "keep one on the shelf", and a counted on-hand of 1 or
        # more cancels it out. When on-hand is zero it does buy a full pack of a
        # dead SKU, so the line is flagged.
        safety = max(
            forecast_over_cover * self.config.safety_stock_fraction,
            self.config.safety_stock_floor,
        )

        post_cutoff: dict[str, object]
        effective_on_hand = on_hand
        if profile is not None and on_hand > 0:
            projection = project_sales(
                product,
                projection_start,
                plan.delivery,
                self.baseline,
                self.multipliers,
                profile,
                contexts=calendar,
                cutoff_hour=self.config.business_day_cutoff_hour,
            )
            effective_on_hand = on_hand - projection.units
            post_cutoff = {"available": True, **projection.to_dict()}
        else:
            post_cutoff = {
                "available": False,
                "reason": profile_error
                or ("no counted on-hand to adjust" if on_hand <= 0 else "no hourly profile"),
                "from": projection_start.isoformat(),
                "to": plan.delivery.isoformat(),
            }

        need = forecast_over_cover + safety - effective_on_hand - on_order
        warnings: list[str] = []
        caps: dict[str, object] = {}
        capped_units = need
        if product.max_order_units is not None and need > product.max_order_units:
            capped_units = product.max_order_units
            caps["max_order_units"] = product.max_order_units
            caps["uncapped_need_units"] = round(need, 4)
            warnings.append(
                f"Need of {need:.1f} {product.unit_label}s exceeds the {product.max_order_units:g} "
                "cap on this delivery."
            )

        packs = packs_for_units(capped_units, product.pack_size)
        if packs > 0 and forecast_over_cover <= 0:
            warnings.append(
                "No forecast demand over this cover window. The quantity comes entirely from "
                f"the {self.config.safety_stock_floor:g}-unit safety floor, rounded up to a pack "
                f"of {product.pack_size:g}. Check the count and the mapping before sending."
            )
        if vendor.rules.minimum_order_units and packs * product.pack_size < vendor.rules.minimum_order_units and packs > 0:
            packs = int(math.ceil(vendor.rules.minimum_order_units / product.pack_size))
            caps["vendor_minimum_units"] = vendor.rules.minimum_order_units
        order_units = packs * product.pack_size

        notes: list[str] = list(product.notes)
        if product.vendor_confidence != "confirmed":
            notes.append(
                "Vendor assignment for this product is not confirmed against the order guide."
            )
        if product.excluded_from_baseline:
            notes.append(
                "Bottle service: excluded from the trailing baseline and forecast from booked "
                "events only. A zero here means nothing is booked, not that demand is zero."
            )

        baseline_by_weekday = {
            day.day.strftime("%A"): self.baseline.baseline(product.key, day.day.weekday())
            for day in forecast.days
        }

        reasoning = ReasoningRecord(
            product_key=product.key,
            product_name=product.name,
            vendor_key=product.vendor,
            units_sold_last_week=self.units_sold_last_week(product.key),
            baseline_by_weekday=baseline_by_weekday,
            forecast=forecast,
            forecast_over_cover=forecast_over_cover,
            safety_stock=safety,
            counted_on_hand=on_hand,
            post_cutoff=post_cutoff,
            effective_on_hand=effective_on_hand,
            already_on_order=on_order,
            need_units=need,
            pack_size=product.pack_size,
            order_packs=packs,
            order_units=order_units,
            days_of_cover=plan.days_of_cover,
            plan=plan.to_dict(),
            caps=caps,
            notes=notes,
        )
        return OrderLine(
            product=product,
            order_packs=packs,
            order_units=order_units,
            reasoning=reasoning,
            warnings=warnings,
        )
