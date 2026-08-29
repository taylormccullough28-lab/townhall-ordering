"""Load the vendor/product/mapping catalog from editable YAML.

The catalog ships in ``thbev/catalog/data`` and can be overridden wholesale by
pointing :func:`load_catalog` at another directory, so a location or a test can
carry its own data without touching code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import yaml

from ..normalize import normalize_key
from .models import (
    BottleYields,
    Contact,
    ConversionType,
    EngineConfig,
    Mapping,
    MappingKey,
    OrderWindow,
    PourSizes,
    Product,
    Recipe,
    RecipeLine,
    Vendor,
    VendorRules,
    parse_time,
    weekday_index,
)

DATA_DIR = Path(__file__).resolve().parent / "data"


class CatalogError(ValueError):
    """Raised when the catalog data is malformed or internally inconsistent."""


@dataclass
class ModifierRule:
    """How one POS modifier affects depletion.

    ``kind="pour"`` replaces the parent sale's pour size; ``kind="product"``
    adds a depletion line of its own.
    """

    match: str
    kind: str
    pour: str | None = None
    product: str | None = None
    units: float = 1.0

    @property
    def normalized_match(self) -> str:
        return normalize_key(self.match)


@dataclass
class MappingResolution:
    """The outcome of resolving one sale against the catalog."""

    mapping: Mapping | None
    reason: str | None = None
    conflicts: tuple[Mapping, ...] = ()


@dataclass
class Catalog:
    """Vendors, products, mappings, recipes and engine config, loaded together."""

    vendors: dict[str, Vendor] = field(default_factory=dict)
    products: dict[str, Product] = field(default_factory=dict)
    mappings: list[Mapping] = field(default_factory=list)
    recipes: dict[str, Recipe] = field(default_factory=dict)
    modifiers: list[ModifierRule] = field(default_factory=list)
    config: EngineConfig = field(default_factory=EngineConfig)
    unverified_recipes: set[str] = field(default_factory=set)

    # -- lookups -------------------------------------------------------------

    def vendor(self, key: str) -> Vendor:
        """Fetch a vendor by key.

        Raises:
            KeyError: If no such vendor exists.
        """
        if key not in self.vendors:
            raise KeyError(f"Unknown vendor {key!r}. Known: {', '.join(sorted(self.vendors))}.")
        return self.vendors[key]

    def product(self, key: str) -> Product:
        """Fetch a product by key.

        Raises:
            KeyError: If no such product exists.
        """
        if key not in self.products:
            raise KeyError(f"Unknown product {key!r}.")
        return self.products[key]

    def recipe(self, key: str) -> Recipe:
        """Fetch a recipe by key.

        Raises:
            KeyError: If no such recipe exists.
        """
        if key not in self.recipes:
            raise KeyError(f"Unknown recipe {key!r}.")
        return self.recipes[key]

    def products_for_vendor(self, vendor_key: str | None) -> list[Product]:
        """Every product assigned to a vendor (or to no vendor, for None)."""
        return [p for p in self.products.values() if p.vendor == vendor_key]

    def unassigned_products(self) -> list[Product]:
        """Products whose distributor is not yet confirmed."""
        return [p for p in self.products.values() if not p.vendor]

    def resolve_modifier(self, modifier: str) -> ModifierRule | None:
        """Find the rule for a POS modifier string, or None if unclassified."""
        target = normalize_key(modifier)
        for rule in self.modifiers:
            if rule.normalized_match == target:
                return rule
        return None

    def resolve(self, item_key: Sequence[str]) -> MappingResolution:
        """Resolve a normalized four-part POS key to a mapping.

        Args:
            item_key: ``ItemKey.normalized`` -- (category, menu, group, item).

        Returns:
            A :class:`MappingResolution`. ``mapping`` is None when nothing
            matched (the sale belongs in the unmapped queue) or when two equally
            specific mappings both matched, which is a catalog conflict the
            resolver refuses to guess its way through.
        """
        candidates = [m for m in self.mappings if m.matches(item_key)]
        if not candidates:
            return MappingResolution(None, reason="no mapping for composite key")
        best = max(candidates, key=lambda m: m.key.specificity)
        tied = [m for m in candidates if m.key.specificity == best.key.specificity]
        if len(tied) > 1:
            return MappingResolution(
                None,
                reason=(
                    "ambiguous mapping: "
                    f"{len(tied)} equally specific entries match ({'; '.join(str(m.key) for m in tied)})"
                ),
                conflicts=tuple(tied),
            )
        return MappingResolution(best)

    def validate(self) -> list[str]:
        """Return catalog integrity problems as human-readable strings."""
        problems: list[str] = []
        for product in self.products.values():
            if product.vendor and product.vendor not in self.vendors:
                problems.append(
                    f"Product {product.key!r} references unknown vendor {product.vendor!r}."
                )
            if product.pack_size <= 0:
                problems.append(f"Product {product.key!r} has a non-positive pack size.")
        for recipe in self.recipes.values():
            for line in recipe.lines:
                if line.product not in self.products:
                    problems.append(
                        f"Recipe {recipe.key!r} references unknown product {line.product!r}."
                    )
                try:
                    line.amount()
                except ValueError as exc:
                    problems.append(str(exc))
        for mapping in self.mappings:
            if bool(mapping.product) == bool(mapping.recipe):
                problems.append(
                    f"Mapping {mapping.key} must set exactly one of product or recipe."
                )
            if mapping.product and mapping.product not in self.products:
                problems.append(
                    f"Mapping {mapping.key} references unknown product {mapping.product!r}."
                )
            if mapping.recipe and mapping.recipe not in self.recipes:
                problems.append(
                    f"Mapping {mapping.key} references unknown recipe {mapping.recipe!r}."
                )
            if mapping.bundle and mapping.bundle not in self.recipes:
                problems.append(
                    f"Mapping {mapping.key} references unknown bundle {mapping.bundle!r}."
                )
            if mapping.key.specificity == 0:
                problems.append(f"Mapping {mapping.key} constrains nothing; it would match everything.")
        for rule in self.modifiers:
            if rule.kind == "product" and rule.product not in self.products:
                problems.append(
                    f"Modifier {rule.match!r} references unknown product {rule.product!r}."
                )
            if rule.kind not in ("pour", "product"):
                problems.append(f"Modifier {rule.match!r} has unknown kind {rule.kind!r}.")
        return problems


def load_catalog(data_dir: str | Path | None = None) -> Catalog:
    """Load a catalog from a directory of YAML files.

    Args:
        data_dir: Directory holding ``vendors.yaml``, ``products.yaml``,
            ``mappings.yaml`` and ``config.yaml``. Defaults to the packaged seed
            data.

    Returns:
        A validated :class:`Catalog`.

    Raises:
        CatalogError: If a required file is missing or the data is inconsistent.
    """
    directory = Path(data_dir) if data_dir else DATA_DIR
    catalog = Catalog(
        vendors=_load_vendors(_read(directory / "vendors.yaml")),
        config=_load_config(_read(directory / "config.yaml")),
    )
    products_doc = _read(directory / "products.yaml")
    catalog.products = _load_products(products_doc)
    catalog.recipes, catalog.unverified_recipes = _load_recipes(products_doc)
    mappings_doc = _read(directory / "mappings.yaml")
    catalog.mappings = _load_mappings(mappings_doc)
    catalog.modifiers = _load_modifiers(mappings_doc)

    problems = catalog.validate()
    if problems:
        raise CatalogError(
            "Catalog in "
            f"{directory} is inconsistent:\n  - " + "\n  - ".join(problems)
        )
    return catalog


def _read(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CatalogError(f"Catalog file missing: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise CatalogError(f"{path} must contain a YAML mapping at the top level.")
    return data


def _load_vendors(doc: dict[str, Any]) -> dict[str, Vendor]:
    vendors: dict[str, Vendor] = {}
    for entry in doc.get("vendors", []) or []:
        key = entry.get("key")
        if not key:
            raise CatalogError(f"Vendor entry without a key: {entry!r}")
        windows = tuple(_load_window(w, key) for w in entry.get("windows", []) or [])
        rules_doc = entry.get("rules", {}) or {}
        emergency = rules_doc.get("emergency_contact")
        rules = VendorRules(
            email_only=bool(rules_doc.get("email_only", False)),
            order_email=rules_doc.get("order_email"),
            route_through=rules_doc.get("route_through"),
            routed_contact_hidden_unless=rules_doc.get("routed_contact_hidden_unless"),
            style_only=bool(rules_doc.get("style_only", False)),
            style_unit=rules_doc.get("style_unit"),
            keg_return_required=bool(rules_doc.get("keg_return_required", False)),
            delivery_note=rules_doc.get("delivery_note"),
            minimum_order_units=float(rules_doc.get("minimum_order_units", 0) or 0),
            cover_buffer_days=int(rules_doc.get("cover_buffer_days", 0) or 0),
            emergency_contact=Contact(**emergency) if emergency else None,
            notes=list(rules_doc.get("notes", []) or []),
        )
        contact_doc = entry.get("contact") or None
        vendors[key] = Vendor(
            key=key,
            name=entry.get("name", key),
            channel=entry.get("channel", "phone"),
            contact=Contact(**contact_doc) if contact_doc else None,
            windows=windows,
            rules=rules,
        )
    if not vendors:
        raise CatalogError("vendors.yaml defined no vendors.")
    return vendors


def _load_window(doc: dict[str, Any], vendor_key: str) -> OrderWindow:
    try:
        return OrderWindow(
            key=doc.get("key") or f"{vendor_key}_{doc.get('order_weekday')}",
            order_weekday=weekday_index(doc["order_weekday"]),
            order_time=parse_time(doc["order_time"]),
            delivery_weekday=weekday_index(doc["delivery_weekday"]),
            delivery_time=parse_time(doc.get("delivery_time", "09:00")),
            optional=bool(doc.get("optional", False)),
            requires_confirmation=bool(doc.get("requires_confirmation", False)),
            confirm_with=doc.get("confirm_with"),
            note=doc.get("note"),
        )
    except (KeyError, ValueError) as exc:
        raise CatalogError(f"Bad order window on vendor {vendor_key}: {exc}") from exc


def _load_products(doc: dict[str, Any]) -> dict[str, Product]:
    products: dict[str, Product] = {}
    for entry in doc.get("products", []) or []:
        key = entry.get("key")
        if not key:
            raise CatalogError(f"Product entry without a key: {entry!r}")
        if key in products:
            raise CatalogError(f"Duplicate product key {key!r}.")
        try:
            conversion = ConversionType(entry.get("conversion", "packaged"))
        except ValueError as exc:
            raise CatalogError(f"Product {key!r}: {exc}") from exc
        products[key] = Product(
            key=key,
            name=entry.get("name", key),
            vendor=entry.get("vendor") or None,
            category=entry.get("category", "unclassified"),
            conversion=conversion,
            pack_size=float(entry.get("pack_size", 1) or 1),
            unit_size_oz=(
                float(entry["unit_size_oz"]) if entry.get("unit_size_oz") is not None else None
            ),
            unit_label=entry.get("unit_label", "unit"),
            pack_label=entry.get("pack_label", "case"),
            keg_size=entry.get("keg_size"),
            default_pour_oz=(
                float(entry["default_pour_oz"]) if entry.get("default_pour_oz") is not None else None
            ),
            par=float(entry["par"]) if entry.get("par") is not None else None,
            order_critical=bool(entry.get("order_critical", False)),
            excluded_from_baseline=bool(entry.get("excluded_from_baseline", False)),
            max_order_units=(
                float(entry["max_order_units"]) if entry.get("max_order_units") is not None else None
            ),
            vendor_confidence=entry.get("vendor_confidence", "unconfirmed"),
            style=entry.get("style"),
            notes=list(entry.get("notes", []) or []),
        )
    if not products:
        raise CatalogError("products.yaml defined no products.")
    return products


def _load_recipes(doc: dict[str, Any]) -> tuple[dict[str, Recipe], set[str]]:
    recipes: dict[str, Recipe] = {}
    unverified: set[str] = set()
    for entry in doc.get("recipes", []) or []:
        key = entry.get("key")
        if not key:
            raise CatalogError(f"Recipe entry without a key: {entry!r}")
        lines = tuple(
            RecipeLine(
                product=line["product"],
                oz=float(line["oz"]) if line.get("oz") is not None else None,
                units=float(line["units"]) if line.get("units") is not None else None,
            )
            for line in entry.get("lines", []) or []
        )
        if not lines:
            raise CatalogError(f"Recipe {key!r} has no lines.")
        recipes[key] = Recipe(key=key, lines=lines, description=entry.get("description"))
        if entry.get("unverified"):
            unverified.add(key)
    return recipes, unverified


def _load_mappings(doc: dict[str, Any]) -> list[Mapping]:
    mappings: list[Mapping] = []
    for entry in doc.get("mappings", []) or []:
        key_doc = entry.get("key") or {}
        conversion = entry.get("conversion")
        try:
            conversion_type = ConversionType(conversion) if conversion else None
        except ValueError as exc:
            raise CatalogError(f"Mapping {key_doc!r}: {exc}") from exc
        mappings.append(
            Mapping(
                key=MappingKey(
                    sales_category=key_doc.get("sales_category"),
                    menu=key_doc.get("menu"),
                    menu_group=key_doc.get("menu_group"),
                    menu_item=key_doc.get("menu_item"),
                ),
                product=entry.get("product"),
                recipe=entry.get("recipe"),
                factor=float(entry.get("factor", 1) or 1),
                pour_oz=float(entry["pour_oz"]) if entry.get("pour_oz") is not None else None,
                bundle=entry.get("bundle"),
                conversion=conversion_type,
                bottle_service=bool(entry.get("bottle_service", False)),
                notes=list(entry.get("notes", []) or []),
            )
        )
    return mappings


def _load_modifiers(doc: dict[str, Any]) -> list[ModifierRule]:
    rules: list[ModifierRule] = []
    for entry in doc.get("modifiers", []) or []:
        rules.append(
            ModifierRule(
                match=entry["match"],
                kind=entry.get("kind", "pour"),
                pour=entry.get("pour"),
                product=entry.get("product"),
                units=float(entry.get("units", 1) or 1),
            )
        )
    return rules


def _load_config(doc: dict[str, Any]) -> EngineConfig:
    pours_doc = doc.get("pours", {}) or {}
    yields_doc = doc.get("yields", {}) or {}
    return EngineConfig(
        location=doc.get("location", "Townhall - Short North"),
        business_day_cutoff_hour=int(doc.get("business_day_cutoff_hour", 4)),
        pours=PourSizes(
            single=float(pours_doc.get("single", 1.5)),
            rocks=float(pours_doc.get("rocks", 2.5)),
            double=float(pours_doc.get("double", 3.0)),
            default=str(pours_doc.get("default", "single")),
        ),
        yields=BottleYields(
            ml_750=float(yields_doc.get("ml_750", 25.36)),
            ml_1000=float(yields_doc.get("ml_1000", 33.81)),
            ml_1750=float(yields_doc.get("ml_1750", 59.17)),
            half_barrel_oz=float(yields_doc.get("half_barrel_oz", 1880)),
            sixth_barrel_oz=float(yields_doc.get("sixth_barrel_oz", 627)),
        ),
        overpour_factor=float(doc.get("overpour_factor", 0.05)),
        wine_glass_oz=float(doc.get("wine_glass_oz", 5.0)),
        draft_pour_oz=float(doc.get("draft_pour_oz", 16.0)),
        safety_stock_fraction=float(doc.get("safety_stock_fraction", 0.25)),
        safety_stock_floor=float(doc.get("safety_stock_floor", 1.0)),
        baseline_weeks=int(doc.get("baseline_weeks", 4)),
        baseline_trim=str(doc.get("baseline_trim", "high_low")),
        event_multipliers=doc.get("event_multipliers", {}) or {},
        weather_multipliers=doc.get("weather_multipliers", {}) or {},
        buyout_per_head_units=doc.get("buyout_per_head_units", {}) or {},
        superior_second_window_threshold=float(doc.get("superior_second_window_threshold", 0.20)),
        post_cutoff_fallback=str(doc.get("post_cutoff_fallback", "error")),
    )
