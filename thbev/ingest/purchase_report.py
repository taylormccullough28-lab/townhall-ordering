"""Parser for MarginEdge Purchase Report CSV exports.

Observed header, verbatim (note the **empty third column name**)::

    Restaurant,Product,,Category,Report By,Purchased Units,Purchased Amount,Avg Cost

This is a *purchasing* file, not a sales file, so it produces
:class:`PurchaseLine` rather than ``SalesRow``. It is aggregated over the whole
report period -- there are no dates and no invoice numbers -- so it can seed a
catalog and a purchase rate, but it cannot supply a reorder rhythm and it is not
a substitute for sales data.

**It carries no vendor column.** Product-to-distributor mapping is not
recoverable from this report; a different MarginEdge export is needed.

Four file-specific hazards, all handled here:

* **The GL-account column has no header.** It sits between ``Product`` and
  ``Category`` and holds values like ``COGS Liquor`` / ``COGS Beer Draft``. It
  cannot be matched by name, so it is resolved positionally *relative to two
  named neighbours* rather than by a hardcoded index.
* **Credits are accounting negatives** -- ``(385.00)`` and ``-154`` units. These
  are deposit returns, and they must stay negative: they are how keg-credit
  capture gets measured.
* **The unit-of-measure field is contaminated with product names.** Alongside
  clean values like ``Bottle (750 Milliliters)`` sit entries like
  ``OYO 750mL (Bottle)`` and ``Michelob Ultra (Can)``, where the product name
  has leaked into the unit. See :func:`parse_unit`.
* **Deposit lines are not products.** ``Keg Deposit - At Purchase $30`` is a
  charge, not something anyone orders. They are classified out into
  ``deposits`` so they neither pollute the catalog nor get ordered.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from ..models import Issue, Severity
from ..normalize import clean_text, normalize_header, normalize_key, parse_number

#: GL accounts that represent beverage purchasing.
BEVERAGE_GL_ACCOUNTS: frozenset[str] = frozenset(
    {
        "cogs liquor",
        "cogs n/a bev",
        "cogs na bev",
        "cogs beer draft",
        "cogs beer bottle",
        "cogs wine",
        "r&d - liquor",
        "r&d - na bev",
    }
)

#: Unit nouns. When one of these appears as the *trailing parenthetical*, the
#: parenthetical is the real unit and everything before it is contamination.
UNIT_NOUNS: frozenset[str] = frozenset(
    {
        "bottle", "can", "case", "keg", "each", "pound", "quart", "gallon",
        "liter", "ounce", "jar", "bag", "other",
    }
)

OZ_PER_ML = 0.033814
OZ_PER_LITER = 33.814
OZ_PER_GALLON = 128.0

#: Explicit keg geometries seen in the data. Gross volume, before pour loss.
KEG_GROSS_OZ: dict[str, float] = {
    "1/2bbl": 15.5 * OZ_PER_GALLON,   # 1984.0
    "1/4bbl": 7.75 * OZ_PER_GALLON,   # 992.0
    "1/6bbl": 5.16 * OZ_PER_GALLON,   # 660.5
    "50l": 13.2 * OZ_PER_GALLON,      # 1689.6
    "20l": 5.28 * OZ_PER_GALLON,      # 675.8
}

_DEPOSIT_RE = re.compile(r"\bdeposit\b", re.IGNORECASE)
_PAREN_RE = re.compile(r"\(([^)]*)\)")
#: A bare size token ("12oz", "750 mL", "1.75 L") rather than a product name.
_SIZE_ONLY_RE = re.compile(
    r"[\d.]+\s*(?:oz|ounces?|fluid\s*ounces?|ml|milliliters?|l|liters?|gal|gallons?)",
    re.IGNORECASE,
)


@dataclass
class PurchaseLine:
    """One product's aggregate purchasing over the report period."""

    restaurant: str
    product: str
    gl_account: str
    category: str
    unit_raw: str
    unit: str | None
    unit_volume_oz: float | None
    units: float
    amount: float
    avg_cost: float | None
    is_beverage: bool
    is_deposit: bool
    unit_name_contaminated: bool = False

    @property
    def key(self) -> str:
        """Stable slug for this product."""
        return normalize_key(self.product)

    def weekly_rate(self, weeks: float) -> float:
        """Average units purchased per week over the report period."""
        return self.units / weeks if weeks > 0 else 0.0


@dataclass
class PurchaseReportResult:
    """Everything one purchase report produced, including what it could not use."""

    lines: list[PurchaseLine] = field(default_factory=list)
    deposits: list[PurchaseLine] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    restaurants: set[str] = field(default_factory=set)
    source_file: str | None = None
    counters: dict[str, int] = field(default_factory=dict)

    def bump(self, name: str, amount: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + amount

    def add_issue(self, severity: Severity, code: str, message: str, **context: Any) -> None:
        self.issues.append(Issue(severity=severity, code=code, message=message, context=context))

    @property
    def beverage_lines(self) -> list[PurchaseLine]:
        return [line for line in self.lines if line.is_beverage]


def parse_unit(raw: Any) -> tuple[str | None, float | None, bool]:
    """Resolve a ``Report By`` cell into (unit, volume_in_oz, was_contaminated).

    Handles the three observed shapes::

        "Bottle (750 Milliliters)"  -> ("Bottle", 25.36, False)
        "OYO 750mL (Bottle)"        -> ("Bottle", 25.36, True)   # name leaked in
        "Keg (1/6BBL) 5.16GAL"      -> ("Keg",    660.5, False)

    The disambiguation rule: if the trailing parenthetical is itself a unit
    noun, the parenthetical is the unit and the prefix is product-name
    contamination. Otherwise the prefix is the unit and the parenthetical
    qualifies its size.
    """
    text = clean_text(raw)
    if not text:
        return None, None, False

    parens = [p.strip() for p in _PAREN_RE.findall(text)]
    outside = _PAREN_RE.sub(" ", text).strip()
    contaminated = False
    unit: str | None = None

    # Order matters. Text OUTSIDE the parentheses wins when it is itself a unit
    # noun -- "Bottle (Liter)" is a litre bottle, not a unit called "Liter".
    # Only when the outside text is *not* a unit do we conclude the product
    # name has leaked in and the parenthetical carries the real unit.
    if outside:
        if normalize_key(outside) in UNIT_NOUNS:
            unit = outside
        elif normalize_key(outside.split()[0]) in UNIT_NOUNS:
            unit = outside.split()[0]
        elif parens and normalize_key(parens[-1]) in UNIT_NOUNS:
            unit = parens[-1]
            # "12oz (Bottle)" is a size qualifier, not contamination.
            # "Michelob Ultra (Can)" is a product name that leaked in.
            contaminated = not _SIZE_ONLY_RE.fullmatch(outside)
        else:
            unit = outside
    elif parens:
        unit = parens[-1] if normalize_key(parens[-1]) in UNIT_NOUNS else parens[0]

    return unit, _volume_oz(text), contaminated


def _volume_oz(text: str) -> float | None:
    """Best-effort volume in fluid ounces for a unit-of-measure string."""
    low = text.lower().replace(" ", "")

    for token, oz in KEG_GROSS_OZ.items():
        if token in low:
            return oz

    match = re.search(r"([\d.]+)\s*(?:fluid\s*ounce|floz|oz)", text, re.IGNORECASE)
    if match:
        return _safe_float(match.group(1))
    match = re.search(r"([\d.]+)\s*(?:milliliters?|ml)\b", text, re.IGNORECASE)
    if match:
        value = _safe_float(match.group(1))
        return value * OZ_PER_ML if value else None
    match = re.search(r"([\d.]+)\s*(?:gal|gallon)", text, re.IGNORECASE)
    if match:
        value = _safe_float(match.group(1))
        return value * OZ_PER_GALLON if value else None
    if re.search(r"\bliter\b|\bl\b", low):
        match = re.search(r"([\d.]+)\s*l\b", low)
        if match:
            value = _safe_float(match.group(1))
            return value * OZ_PER_LITER if value else None
        if "liter" in low:
            return OZ_PER_LITER
    if "quart" in low:
        return 32.0
    return None


def _safe_float(text: str) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _resolve_gl_column(header: list[str]) -> int | None:
    """Locate the unnamed GL-account column between ``Product`` and ``Category``.

    Resolved relative to its named neighbours rather than by a fixed index, so
    a reordered or extra-column export still lands correctly.
    """
    normalized = [normalize_header(cell_value) for cell_value in header]
    try:
        product_at = normalized.index("product")
    except ValueError:
        return None
    for index in range(product_at + 1, len(normalized)):
        if not normalized[index]:
            return index
        if normalized[index] in {"category", "sub category", "subcategory"}:
            break
    return None


def parse_purchase_report(
    path: str | Path,
    *,
    restaurant: str | None = None,
    beverage_accounts: Iterable[str] | None = None,
) -> PurchaseReportResult:
    """Parse a MarginEdge Purchase Report CSV.

    Args:
        path: CSV file to read.
        restaurant: When given, keep only rows for this restaurant. The account
            spans many units and mixing them silently corrupts every rate.
        beverage_accounts: Override the GL accounts treated as beverage.
    """
    path = Path(path)
    accounts = frozenset(
        normalize_key(a) for a in (beverage_accounts or BEVERAGE_GL_ACCOUNTS)
    )
    result = PurchaseReportResult(source_file=str(path))

    # utf-8-sig: the observed export carries a BOM.
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))

    if not rows:
        result.add_issue(Severity.ERROR, "empty_file", f"{path.name} contains no rows")
        return result

    header = rows[0]
    normalized = [normalize_header(c) for c in header]
    gl_index = _resolve_gl_column(header)
    if gl_index is None:
        result.add_issue(
            Severity.ERROR,
            "missing_gl_column",
            "Could not locate the unnamed GL-account column after 'Product'. "
            "Beverage classification is impossible without it; refusing to guess.",
            header=header,
        )
        return result

    def index_of(*names: str) -> int | None:
        for name in names:
            if name in normalized:
                return normalized.index(name)
        return None

    idx = {
        "restaurant": index_of("restaurant", "location"),
        "product": index_of("product", "item"),
        "category": index_of("category", "sub category"),
        "unit": index_of("report by", "unit", "uom"),
        "units": index_of("purchased units", "units", "qty"),
        "amount": index_of("purchased amount", "amount", "total"),
        "avg_cost": index_of("avg cost", "average cost", "unit cost"),
    }
    for field_name, position in idx.items():
        if position is None:
            result.add_issue(
                Severity.WARNING,
                "missing_column",
                f"Column for '{field_name}' not found; that field will be empty.",
            )

    def get(row: list[str], field_name: str) -> Any:
        position = idx[field_name]
        if position is None or position >= len(row):
            return None
        return row[position]

    for row in rows[1:]:
        if not any(str(c).strip() for c in row):
            continue

        row_restaurant = clean_text(get(row, "restaurant")) or ""
        result.restaurants.add(row_restaurant)
        if restaurant and normalize_key(row_restaurant) != normalize_key(restaurant):
            result.bump("rows_other_restaurant")
            continue

        product = clean_text(get(row, "product"))
        if not product:
            result.bump("rows_no_product")
            continue

        gl_account = clean_text(row[gl_index] if gl_index < len(row) else None) or ""
        unit_raw = clean_text(get(row, "unit")) or ""
        unit, volume_oz, contaminated = parse_unit(unit_raw)
        if contaminated:
            result.bump("unit_name_contaminated")

        units = parse_number(get(row, "units")) or 0.0
        amount = parse_number(get(row, "amount")) or 0.0
        avg_cost = parse_number(get(row, "avg_cost"))

        line = PurchaseLine(
            restaurant=row_restaurant,
            product=product,
            gl_account=gl_account,
            category=clean_text(get(row, "category")) or "",
            unit_raw=unit_raw,
            unit=unit,
            unit_volume_oz=volume_oz,
            units=units,
            amount=amount,
            avg_cost=avg_cost,
            is_beverage=normalize_key(gl_account) in accounts,
            is_deposit=bool(_DEPOSIT_RE.search(product)),
            unit_name_contaminated=contaminated,
        )

        if line.is_deposit:
            result.deposits.append(line)
            result.bump("deposit_lines")
        else:
            result.lines.append(line)
            if line.is_beverage:
                result.bump("beverage_lines")

        if units < 0 or amount < 0:
            result.bump("credit_lines")

    if len(result.restaurants) > 1 and not restaurant:
        result.add_issue(
            Severity.WARNING,
            "multiple_restaurants",
            "Report spans multiple restaurants and no filter was given; "
            "rates will mix locations.",
            restaurants=sorted(result.restaurants),
        )

    return result


def keg_deposit_balance(result: PurchaseReportResult) -> dict[str, float]:
    """Deposits charged vs. returned, from the deposit lines.

    A large unreturned balance is the keg-credit leak the order guide warns
    about, in dollars. Note this is a period snapshot: kegs bought near the end
    of the window have not had time to come back, so some gap is timing, not
    loss.
    """
    charged = returned = charged_amount = returned_amount = 0.0
    for line in result.deposits:
        if "keg" not in line.product.lower():
            continue
        if line.units >= 0:
            charged += line.units
            charged_amount += line.amount
        else:
            returned += -line.units
            returned_amount += -line.amount
    return {
        "charged_units": charged,
        "returned_units": returned,
        "outstanding_units": charged - returned,
        "charged_amount": charged_amount,
        "returned_amount": returned_amount,
        "outstanding_amount": charged_amount - returned_amount,
        "return_rate": (returned / charged) if charged else 0.0,
    }
