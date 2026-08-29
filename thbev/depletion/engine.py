"""Turn normalized POS sales into product depletion.

The POS sells menu items; vendors sell SKUs. This module is the conversion
between them, and it is where the numbers most easily go quietly wrong. Four
things it refuses to do:

* treat a bottle-service sale as a pour (undercounts that spirit tenfold),
* count a sale it cannot map (those go to the unmapped queue with quantities),
* apply the overpour factor to keg yields (the PRD's keg figures are already
  net of the ~5% foam and line loss),
* silently default a pour size without saying so (no modifier data exists yet,
  so every spirit sale currently defaults to a 1.5 oz Single).
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable

from ..catalog.loader import Catalog
from ..catalog.models import INDIRECT_ONLY, ConversionType, Mapping, Product
from ..models import Issue, ItemKey, SalesRow, Severity, UnmappedRow


@dataclass
class DepletionLine:
    """One product's depletion attributable to one sale.

    ``units`` is always in the product's ordering unit -- bottles, cans, kegs --
    so order quantities never have to re-derive it. ``oz`` is kept alongside for
    the liquid conversions, because a partial bottle is meaningful and a
    rounded-up bottle count is not.
    """

    product_key: str
    units: float
    conversion: ConversionType
    qty_sold: float
    key: ItemKey
    oz: float | None = None
    business_date: date | None = None
    sold_at: datetime | None = None
    comped: bool = False
    bottle_service: bool = False
    via: str = "direct"
    pour_oz: float | None = None
    pour_name: str | None = None
    source_row: int | None = None


@dataclass
class DepletionResult:
    """Depletion for a set of sales, plus everything that could not be converted."""

    lines: list[DepletionLine] = field(default_factory=list)
    unmapped: list[UnmappedRow] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=dict)

    def bump(self, name: str, amount: int = 1) -> None:
        """Increment a named counter."""
        self.counters[name] = self.counters.get(name, 0) + amount

    def add_issue(self, severity: Severity, code: str, message: str, **context) -> None:
        """Record an observation about the conversion."""
        self.issues.append(Issue(severity, code, message, context))

    def units_by_product(self, *, include_bottle_service: bool = True) -> dict[str, float]:
        """Total depleted units per product key."""
        totals: dict[str, float] = defaultdict(float)
        for line in self.lines:
            if not include_bottle_service and line.bottle_service:
                continue
            totals[line.product_key] += line.units
        return dict(totals)

    def daily_units(
        self, *, include_bottle_service: bool = True
    ) -> dict[tuple[str, date], float]:
        """Units per (product, business date). Undated lines are skipped."""
        totals: dict[tuple[str, date], float] = defaultdict(float)
        for line in self.lines:
            if line.business_date is None:
                continue
            if not include_bottle_service and line.bottle_service:
                continue
            totals[(line.product_key, line.business_date)] += line.units
        return dict(totals)

    def hourly_units(self, product_key: str) -> list[tuple[datetime, float]]:
        """Timestamped depletion for one product, for post-cutoff proration."""
        return [
            (line.sold_at, line.units)
            for line in self.lines
            if line.product_key == product_key and line.sold_at is not None
        ]

    @property
    def comped_units(self) -> dict[str, float]:
        """Comped depletion per product -- counted, but reported separately."""
        totals: dict[str, float] = defaultdict(float)
        for line in self.lines:
            if line.comped:
                totals[line.product_key] += line.units
        return dict(totals)

    @property
    def bottle_service_units(self) -> dict[str, float]:
        """Bottle-service depletion per product, excluded from the trailing baseline."""
        totals: dict[str, float] = defaultdict(float)
        for line in self.lines:
            if line.bottle_service:
                totals[line.product_key] += line.units
        return dict(totals)

    def summary(self) -> dict[str, object]:
        """Machine-readable summary for the CLI and logs."""
        return {
            "lines": len(self.lines),
            "products_touched": len(self.units_by_product()),
            "units_by_product": self.units_by_product(),
            "bottle_service_units": self.bottle_service_units,
            "comped_units": self.comped_units,
            "unmapped_rows": len(self.unmapped),
            "unmapped_qty": sum(u.qty or 0.0 for u in self.unmapped),
            "counters": dict(self.counters),
            "issues": [
                {"severity": i.severity.value, "code": i.code, "message": i.message}
                for i in self.issues
            ],
        }


class DepletionEngine:
    """Converts sales rows to product depletion using a catalog."""

    def __init__(self, catalog: Catalog) -> None:
        self.catalog = catalog
        self.config = catalog.config

    # -- yields ---------------------------------------------------------------

    def keg_yield_oz(self, product: Product) -> float:
        """Usable ounces in a keg of this product's size.

        The PRD's keg figures (1/2 bbl about 1,880 oz, 1/6 bbl about 627 oz) are
        already net of the ~5% foam and line loss, so the overpour factor is
        deliberately NOT applied on top of them.

        Raises:
            ValueError: If the product has no recognized keg size.
        """
        sizes = {
            "half_barrel": self.config.yields.half_barrel_oz,
            "sixth_barrel": self.config.yields.sixth_barrel_oz,
            "1/2 bbl": self.config.yields.half_barrel_oz,
            "1/6 bbl": self.config.yields.sixth_barrel_oz,
        }
        if product.unit_size_oz:
            return product.unit_size_oz
        key = (product.keg_size or "").strip().lower()
        if key not in sizes:
            raise ValueError(
                f"Draft product {product.key!r} has no keg_size (expected half_barrel or "
                "sixth_barrel) and no unit_size_oz; keg yield cannot be computed."
            )
        return sizes[key]

    def bottle_yield_oz(self, product: Product) -> float:
        """Effective ounces per bottle, after the overpour factor.

        Raises:
            ValueError: If the product has no bottle size.
        """
        if not product.unit_size_oz:
            raise ValueError(
                f"Product {product.key!r} needs unit_size_oz to convert ounces to bottles "
                "(750ml = 25.36, 1L = 33.81, 1.75L = 59.17)."
            )
        return self.config.effective_yield_oz(product.unit_size_oz)

    # -- conversion -----------------------------------------------------------

    def deplete(self, rows: Iterable[SalesRow]) -> DepletionResult:
        """Convert sales rows into depletion lines.

        Args:
            rows: Normalized sales rows from any :class:`SalesSource`.

        Returns:
            A :class:`DepletionResult`. Rows with no catalog mapping, ambiguous
            mappings, or misconfigured conversions are preserved in ``unmapped``
            with their quantities, never dropped.
        """
        result = DepletionResult()
        if self.catalog.unverified_recipes:
            result.add_issue(
                Severity.WARNING,
                "unverified_recipes",
                "These recipes are placeholders, not house specs: "
                + ", ".join(sorted(self.catalog.unverified_recipes))
                + ". Spirit and prep-ingredient forecasts built on them are not trustworthy.",
            )

        for row in rows:
            if row.voided:
                result.bump("voided_rows_skipped")
                continue

            resolution = self.catalog.resolve(row.key.normalized)
            if resolution.mapping is None:
                result.unmapped.append(
                    UnmappedRow(
                        reason=resolution.reason or "unmapped",
                        qty=row.qty,
                        source=row.source,
                        row_number=row.row_number,
                        key=row.key,
                        raw=dict(row.raw),
                    )
                )
                result.bump("unmapped_rows")
                continue

            try:
                self._apply_mapping(row, resolution.mapping, result)
            except ValueError as exc:
                result.unmapped.append(
                    UnmappedRow(
                        reason=f"conversion error: {exc}",
                        qty=row.qty,
                        source=row.source,
                        row_number=row.row_number,
                        key=row.key,
                        raw=dict(row.raw),
                    )
                )
                result.bump("conversion_errors")
                continue

            self._apply_modifiers(row, result)

        return result

    def _apply_mapping(self, row: SalesRow, mapping: Mapping, result: DepletionResult) -> None:
        conversion = mapping.conversion
        product: Product | None = None
        if mapping.product:
            product = self.catalog.product(mapping.product)
            conversion = conversion or product.conversion
        elif mapping.recipe:
            conversion = conversion or ConversionType.COCKTAIL_RECIPE

        if conversion is None:
            raise ValueError("mapping has no conversion type and no product to infer one from")

        if product is not None and conversion in INDIRECT_ONLY:
            raise ValueError(
                f"product {product.key!r} is a {conversion.value}; it has no POS line of its "
                "own and must be reached through a recipe"
            )

        qty = row.qty * mapping.factor

        if conversion is ConversionType.PACKAGED:
            self._emit(result, row, mapping, product, units=qty, conversion=conversion)

        elif conversion is ConversionType.WHOLE_BOTTLE:
            self._emit(
                result,
                row,
                mapping,
                product,
                units=qty,
                conversion=conversion,
                bottle_service=True,
            )
            if mapping.bundle:
                self._emit_recipe(
                    result, row, mapping, self.catalog.recipe(mapping.bundle), qty,
                    via=f"bundle:{mapping.bundle}", bottle_service=True,
                )
            result.bump("bottle_service_sales")

        elif conversion is ConversionType.DRAFT:
            assert product is not None
            pour = mapping.pour_oz or product.default_pour_oz or self.config.draft_pour_oz
            oz = qty * pour
            units = oz / self.keg_yield_oz(product)
            self._emit(
                result, row, mapping, product, units=units, conversion=conversion,
                oz=oz, pour_oz=pour,
            )

        elif conversion is ConversionType.WINE_GLASS:
            assert product is not None
            pour = mapping.pour_oz or product.default_pour_oz or self.config.wine_glass_oz
            oz = qty * pour
            units = oz / self.bottle_yield_oz(product)
            self._emit(
                result, row, mapping, product, units=units, conversion=conversion,
                oz=oz, pour_oz=pour,
            )

        elif conversion is ConversionType.SPIRIT_POUR:
            assert product is not None
            pour_name, pour = self._pour_for(row, mapping, product, result)
            oz = qty * pour
            units = oz / self.bottle_yield_oz(product)
            self._emit(
                result, row, mapping, product, units=units, conversion=conversion,
                oz=oz, pour_oz=pour, pour_name=pour_name,
            )

        elif conversion is ConversionType.COCKTAIL_RECIPE:
            if not mapping.recipe:
                raise ValueError("cocktail_recipe mapping has no recipe")
            self._emit_recipe(
                result, row, mapping, self.catalog.recipe(mapping.recipe), qty,
                via=f"recipe:{mapping.recipe}",
            )

        else:  # pragma: no cover - INDIRECT_ONLY already rejected above
            raise ValueError(f"unsupported conversion {conversion.value}")

    def _pour_for(
        self, row: SalesRow, mapping: Mapping, product: Product, result: DepletionResult
    ) -> tuple[str, float]:
        """Resolve a spirit pour size from the sale's modifiers.

        With no modifier data in the account, this falls back to the configured
        default (Single, 1.5 oz) and counts how often it had to, so the size of
        the blind spot is visible rather than assumed away.
        """
        if mapping.pour_oz is not None:
            return ("mapping_override", mapping.pour_oz)
        for modifier in row.modifiers:
            rule = self.catalog.resolve_modifier(modifier)
            if rule and rule.kind == "pour" and rule.pour:
                result.bump(f"pour_from_modifier:{rule.pour}")
                return (rule.pour, self.config.pours.size_for(rule.pour))
        result.bump("pour_defaulted")
        default = self.config.pours.default
        return (default, self.config.pours.size_for(default))

    def _emit_recipe(
        self,
        result: DepletionResult,
        row: SalesRow,
        mapping: Mapping,
        recipe,
        qty: float,
        *,
        via: str,
        bottle_service: bool = False,
    ) -> None:
        for line in recipe.lines:
            product = self.catalog.product(line.product)
            kind, amount = line.amount()
            if kind == "units":
                units = qty * amount
                oz = None
            else:
                oz = qty * amount
                units = oz / self.bottle_yield_oz(product)
            self._emit(
                result,
                row,
                mapping,
                product,
                units=units,
                conversion=product.conversion,
                oz=oz,
                via=via,
                bottle_service=bottle_service,
            )

    def _emit(
        self,
        result: DepletionResult,
        row: SalesRow,
        mapping: Mapping,
        product: Product | None,
        *,
        units: float,
        conversion: ConversionType,
        oz: float | None = None,
        pour_oz: float | None = None,
        pour_name: str | None = None,
        via: str = "direct",
        bottle_service: bool = False,
    ) -> None:
        if product is None:
            raise ValueError("cannot emit a depletion line without a product")
        result.lines.append(
            DepletionLine(
                product_key=product.key,
                units=units,
                conversion=conversion,
                qty_sold=row.qty,
                key=row.key,
                oz=oz,
                business_date=row.business_date,
                sold_at=row.sold_at,
                comped=row.comped,
                bottle_service=bottle_service or mapping.bottle_service or product.excluded_from_baseline,
                via=via,
                pour_oz=pour_oz,
                pour_name=pour_name,
                source_row=row.row_number,
            )
        )
        if row.comped:
            result.bump("comped_lines")

    def _apply_modifiers(self, row: SalesRow, result: DepletionResult) -> None:
        """Emit depletion for product-type modifiers; queue anything unclassified."""
        for modifier in row.modifiers:
            rule = self.catalog.resolve_modifier(modifier)
            if rule is None:
                result.unmapped.append(
                    UnmappedRow(
                        reason=f"unclassified modifier {modifier!r}",
                        qty=row.qty,
                        source=row.source,
                        row_number=row.row_number,
                        key=row.key,
                        raw={"modifier": modifier},
                    )
                )
                result.bump("unmapped_modifiers")
                continue
            if rule.kind != "product" or not rule.product:
                continue
            product = self.catalog.product(rule.product)
            result.lines.append(
                DepletionLine(
                    product_key=product.key,
                    units=row.qty * rule.units,
                    conversion=product.conversion,
                    qty_sold=row.qty,
                    key=row.key,
                    business_date=row.business_date,
                    sold_at=row.sold_at,
                    comped=row.comped,
                    via=f"modifier:{modifier}",
                    source_row=row.row_number,
                )
            )


def packs_for_units(units: float, pack_size: float) -> int:
    """Round a unit count UP to whole packs.

    Raises:
        ValueError: If ``pack_size`` is not positive.
    """
    if pack_size <= 0:
        raise ValueError(f"pack_size must be positive, got {pack_size}")
    if units <= 0:
        return 0
    return int(math.ceil(round(units / pack_size, 9)))
