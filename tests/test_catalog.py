"""Catalog loading and composite-key mapping resolution."""

from __future__ import annotations

import pytest
import yaml

from thbev.catalog import ConversionType, load_catalog
from thbev.catalog.loader import CatalogError


def test_seed_catalog_loads_and_validates(seed_catalog):
    assert seed_catalog.vendors["arena"].rules.email_only
    assert seed_catalog.vendors["oyo"].rules.route_through == "arena"
    assert seed_catalog.vendors["sixth_city"].rules.style_only
    assert seed_catalog.validate() == []


def test_seed_catalog_has_a_vendor_for_every_product(seed_catalog):
    """Gap 3 of CATALOG-COMPLETENESS.md is closed.

    Every product used to carry ``vendor: null`` because the product-to-distributor
    map lived in TH_ORDER_GUIDE.docx, which is not in this repo. The MarginEdge
    vendor-item catalog (pulled 2026-09-28, indexed in vendor_items.yaml) supplies
    it, so nothing is unassigned and nothing is left at ``unconfirmed``.
    """
    assert seed_catalog.unassigned_products() == []
    assert not [
        p.key for p in seed_catalog.products.values()
        if p.vendor_confidence == "unconfirmed"
    ]

    # The ones the PRD states outright keep the stronger "confirmed" label.
    assert seed_catalog.product("oyo_vodka_750").vendor == "arena"
    assert seed_catalog.product("oyo_vodka_750").vendor_confidence == "confirmed"
    assert seed_catalog.product("rotating_sixth_bbl_sixth_city").vendor == "sixth_city"

    # The ones MarginEdge supplied say so, and say which distributor.
    bud = seed_catalog.product("bud_light")
    assert bud.vendor == "columbus_distributing"
    assert bud.vendor_confidence == "marginedge"
    assert seed_catalog.product("suncruiser").vendor == "superior"
    assert seed_catalog.product("red_bull").vendor == "southern_glazers"
    assert seed_catalog.product("chinola").vendor == "heidelberg"


def test_dual_sourced_products_record_the_second_distributor(seed_catalog):
    """Real dual-sourcing is advisory, never a second order.

    The catalog models one vendor per product. Where MarginEdge shows a product
    stocked by more than one distributor, the extra ones go in ``alt_vendors`` so
    the fact is not lost, but ``vendor`` stays single and is the distributor the
    invoices show actually being used.
    """
    red_bull = seed_catalog.product("red_bull")
    assert red_bull.vendor == "southern_glazers"
    assert set(red_bull.alt_vendors) == {"arena", "columbus_distributing"}

    # Pamplemousse: Cavalier does carry it (item 12942), contrary to the
    # "Arena only" note, but Arena is the vendor the invoices use.
    pamp = seed_catalog.product("pamplemousse_750")
    assert pamp.vendor == "arena"
    assert pamp.alt_vendors == ("cavalier",)

    # A product is never listed as its own alternate, and every alternate is a
    # vendor the catalog actually knows how to order from.
    for product in seed_catalog.products.values():
        assert product.vendor not in product.alt_vendors
        for alt in product.alt_vendors:
            assert alt in seed_catalog.vendors


def test_composite_key_separates_same_named_items(catalog):
    """One name, two categories, two menus, two entirely different conversions."""
    pour = catalog.resolve(("liquor", "liquor", "tequila", "espolon blanco")).mapping
    bottle = catalog.resolve(
        ("bottle service", "bottle service", "tequila bottles", "espolon blanco")
    ).mapping
    assert pour.product == "espolon_blanco_750"
    assert bottle.product == "espolon_bottle_service"
    assert bottle.bottle_service is True


def test_blank_category_still_resolves_on_menu_structure(catalog):
    """PMIX exports with no Sales Category column must still map."""
    resolved = catalog.resolve(("", "liquor", "tequila", "espolon blanco")).mapping
    assert resolved.product == "espolon_blanco_750"
    bacardi = catalog.resolve(("", "liquor", "rum", "bacardi fb")).mapping
    assert bacardi.product == "bacardi_750"


def test_most_specific_mapping_wins(catalog):
    """A four-part match beats a three-part one; never the other way round."""
    resolved = catalog.resolve(("liquor", "liquor", "tequila", "espolon blanco"))
    assert resolved.mapping.key.specificity == 4


def test_unmapped_key_is_reported_not_guessed(catalog):
    resolution = catalog.resolve(("liquor", "liquor", "shots", "mystery shot"))
    assert resolution.mapping is None
    assert "no mapping" in resolution.reason


def test_ambiguous_mappings_are_refused(tmp_path, catalog):
    """Two equally specific mappings is a catalog bug, not a coin flip."""
    directory = tmp_path / "catalog"
    directory.mkdir()
    from tests.conftest import FIXTURES

    for name in ("vendors.yaml", "products.yaml", "config.yaml"):
        (directory / name).write_text(
            (FIXTURES / "catalog" / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    (directory / "mappings.yaml").write_text(
        yaml.safe_dump(
            {
                "mappings": [
                    {"key": {"menu": "LIQUOR", "menu_item": "Bud Light"}, "product": "bud_light"},
                    {"key": {"sales_category": "Liquor", "menu_item": "Bud Light"}, "product": "nutrl"},
                ]
            }
        ),
        encoding="utf-8",
    )
    conflicted = load_catalog(directory)
    resolution = conflicted.resolve(("liquor", "liquor", "domestics", "bud light"))
    assert resolution.mapping is None
    assert "ambiguous" in resolution.reason
    assert len(resolution.conflicts) == 2


def test_catalog_validation_catches_dangling_references(tmp_path):
    from tests.conftest import FIXTURES

    directory = tmp_path / "catalog"
    directory.mkdir()
    for name in ("vendors.yaml", "products.yaml", "config.yaml"):
        (directory / name).write_text(
            (FIXTURES / "catalog" / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    (directory / "mappings.yaml").write_text(
        yaml.safe_dump({"mappings": [{"key": {"menu_item": "X"}, "product": "does_not_exist"}]}),
        encoding="utf-8",
    )
    with pytest.raises(CatalogError) as excinfo:
        load_catalog(directory)
    assert "does_not_exist" in str(excinfo.value)


def test_missing_catalog_file_raises(tmp_path):
    with pytest.raises(CatalogError):
        load_catalog(tmp_path)


def test_modifier_classification(catalog):
    assert catalog.resolve_modifier("Double").pour == "double"
    assert catalog.resolve_modifier("  double ").pour == "double"
    assert catalog.resolve_modifier("Add Red Bull").kind == "product"
    assert catalog.resolve_modifier("Extra Dirty") is None


def test_pour_sizes_are_the_confirmed_house_pours(seed_catalog):
    pours = seed_catalog.config.pours
    assert (pours.single, pours.rocks, pours.double) == (1.5, 2.5, 3.0)
    assert pours.default == "single"
    with pytest.raises(KeyError):
        pours.size_for("triple")


def test_effective_yield_applies_overpour(seed_catalog):
    config = seed_catalog.config
    assert config.overpour_factor == 0.05
    assert config.effective_yield_oz(25.36) == pytest.approx(25.36 / 1.05)


def test_prep_ingredients_are_indirect_only(seed_catalog):
    assert seed_catalog.product("chinola").conversion is ConversionType.PREP_INGREDIENT


class TestNamedSkusAndSeasonalProducts:
    """Cavalier is style-only, but carries specific products too.

    A named SKU must survive the rotating-line collapse, or the manager never
    sees the product on the order sheet.
    """

    def test_named_sku_and_alt_vendors_load(self):
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        bumble = catalog.products["fat_heads_bumble_berry"]
        assert bumble.vendor == "cavalier"
        assert bumble.named_sku is True
        assert bumble.keg_size == "half_barrel"

        # Pamplemousse is a 750ml liqueur ordered from Arena. MarginEdge shows
        # Cavalier stocks it too (item 12942), so Cavalier is an alt_vendor - but
        # it must not become Cavalier's product, or the rotating-line collapse
        # would swallow a named liqueur into a keg style-and-count.
        pamp = catalog.products["pamplemousse_750"]
        assert pamp.vendor == "arena"
        assert pamp.unit_size_oz == 25.36
        assert pamp.alt_vendors == ("cavalier",)
        assert "pamplemousse" not in {
            k for k, p in catalog.products.items() if p.vendor == "cavalier"
        }

    def test_superior_second_window_is_wednesday(self):
        from thbev.catalog.loader import load_catalog

        catalog = load_catalog()
        keys = {w.key for w in catalog.vendors["superior"].windows}
        assert "superior_wednesday" in keys
        assert "superior_thursday" not in keys
        wed = next(w for w in catalog.vendors["superior"].windows if w.key == "superior_wednesday")
        assert wed.order_weekday == 2          # Wednesday
        assert wed.delivery_weekday == 4       # Friday
        assert str(wed.order_time).startswith("19:00")
